import asyncio
import random
import re
import uuid
import logging
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from dependencies import get_db
from services.llm_engine import generate_reactivation_drafts
from services.redis_client import redis_db

logger = logging.getLogger(__name__)

# Import our new Mock Enrichment Clients
from services.enrichment.apollo import ApolloMockClient
from services.enrichment.crunchbase import CrunchbaseMockClient
from services.enrichment.bombora import BomboraMockClient

router = APIRouter()

# Instantiate the clients once
apollo_client = ApolloMockClient()
crunchbase_client = CrunchbaseMockClient()
bombora_client = BomboraMockClient()

def calculate_plie_score(apollo_data, crunchbase_data, bombora_data):
    """
    Mathematical scoring engine based on B2B SaaS Firmographics & Intent.
    Returns a score from 0-100 and a natural language explanation.
    """
    score = 30 # Base score for being in our ICP
    reasons = []
    
    # 1. Firmographic Signals (Apollo)
    if apollo_data:
        if 50 <= apollo_data.get('headcount_current', 0) <= 500:
            score += 20
            reasons.append("Headcount in sweet spot (50-500)")
        if apollo_data.get('headcount_growth_pct', 0) > 15.0:
            score += 15
            reasons.append(f"High growth ({apollo_data['headcount_growth_pct']}%)")
            
    # 2. Financial Signals (Crunchbase)
    if crunchbase_data:
        score += 15
        reasons.append(f"Funded: {crunchbase_data.get('funding_stage')}")
        
    # 3. Buying Intent Signals (Bombora)
    if bombora_data and bombora_data.get('is_spiking'):
        score += 20
        reasons.append(f"Spiking intent on {bombora_data.get('top_topic')}")
        
    explanation = " | ".join(reasons) if reasons else "Cold outbound target. Lacks strong signals."
    
    # Cap score between 0 and 100
    final_score = max(0, min(100, score))
    return final_score, explanation

async def process_single_lead(lead_dict: dict, job_id: str):
    """Orchestrates parallel enrichment, scoring, and LLM generation for ONE lead."""
    # UX Theater: Simulate real-world external API latency (Apollo, Crunchbase, etc.)
    await asyncio.sleep(random.uniform(1.0, 7.0))
    
    domain = lead_dict['domain']
    
    # UX Theater Safety Catch: Sanitize the salt from the domain before hitting mock APIs
    clean_domain = re.sub(r'^\d{5}\.', '', domain)
    
    # 1. Fire all 3 Enrichment APIs in PARALLEL for this specific lead
    apollo_task = apollo_client.get_company_data(clean_domain)
    crunchbase_task = crunchbase_client.get_funding_data(clean_domain)
    bombora_task = bombora_client.get_intent_data(clean_domain)
    
    apollo_data, crunchbase_data, bombora_data = await asyncio.gather(
        apollo_task, crunchbase_task, bombora_task, return_exceptions=True
    )
    
    # Safely handle any API failures (graceful degradation)
    apollo_data = apollo_data if not isinstance(apollo_data, Exception) else None
    crunchbase_data = crunchbase_data if not isinstance(crunchbase_data, Exception) else None
    bombora_data = bombora_data if not isinstance(bombora_data, Exception) else None

    # 2. Calculate the ICP Score based on aggregated data
    score, explanation = calculate_plie_score(apollo_data, crunchbase_data, bombora_data)
    
    # 3. Inject the enriched data back into the dictionary so the LLM can see it
    lead_dict['score_explanation'] = explanation
    lead_dict['apollo_data'] = apollo_data
    lead_dict['crunchbase_data'] = crunchbase_data
    lead_dict['bombora_data'] = bombora_data
    
    # 4. Call OpenAI to generate the 3 B2B outreach variants
    drafts = await generate_reactivation_drafts(lead_dict)
    
    # 5. Increment the Redis progress counter exactly as this lead finishes
    if job_id:
        await redis_db.hincrby(f"job:{job_id}", "completed", 1)
    
    if drafts:
        return {
            "id": lead_dict['id'],
            "score": score,
            "explanation": explanation,
            "drafts": drafts,
            # We return these so we can save the raw firmographics to the database
            "headcount": apollo_data.get('headcount_current') if apollo_data else None,
            "growth": apollo_data.get('headcount_growth_pct') if apollo_data else None,
            "funding": crunchbase_data.get('funding_stage') if crunchbase_data else None,
            "intent": bombora_data.get('intent_score') if bombora_data else None
        }
    return None

async def run_batch_background(tenant_id: int, batch_size: int, job_id: str, pool):
    """
    Background worker. Receives the application connection pool explicitly —
    it acquires its own connection from the shared pool rather than opening
    a raw single-connection that bypasses pool limits.
    """
    async with pool.acquire() as conn:
        try:
            # Fetch leads who do NOT have a draft yet
            members = await conn.fetch("""
                SELECT id, contact_name as first_name, company_name, domain 
                FROM b2b_leads 
                WHERE tenant_id = $1 AND message_draft_a IS NULL
                LIMIT $2
            """, tenant_id, batch_size)

            if not members:
                await redis_db.hset(f"job:{job_id}", mapping={"status": "complete", "total": 0, "completed": 0})
                # Fix #3: Set TTL even on the empty-batch fast-exit path
                await redis_db.expire(f"job:{job_id}", 86400)
                return

            # Initialize the job in Redis
            await redis_db.hset(f"job:{job_id}", mapping={
                "status": "processing", 
                "total": len(members), 
                "completed": 0
            })

            # 1. Fire ALL Lead Tasks simultaneously (Nested Parallel Execution)
            tasks = [process_single_lead(dict(record), job_id) for record in members]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 2. Filter out failures and format for bulk DB update
            successful_updates = []
            for result in results:
                if isinstance(result, Exception):
                    logger.warning("Parallel processing error for job %s: %s", job_id, result)
                    continue
                if result:
                    successful_updates.append((
                        result['score'],
                        result['explanation'],
                        result['headcount'],
                        result['growth'],
                        result['funding'],
                        result['intent'],
                        result['drafts']['message_draft_a'],
                        result['drafts']['message_draft_b'],
                        result['drafts']['message_draft_c'],
                        result['id']
                    ))

            # 3. Bulk update the database — Fix #2: wrapped in an explicit
            # transaction so that a mid-write connection loss cannot leave the
            # batch in a partial state. All rows commit together or not at all.
            if successful_updates:
                async with conn.transaction():
                    await conn.executemany("""
                        UPDATE b2b_leads 
                        SET plie_score = $1, 
                            score_explanation = $2,
                            headcount_current = $3,
                            headcount_growth_pct = $4,
                            funding_stage = $5,
                            intent_score = $6,
                            message_draft_a = $7,
                            message_draft_b = $8,
                            message_draft_c = $9,
                            enrichment_status = 'complete'
                        WHERE id = $10
                    """, successful_updates)

            # Mark the job as completely finished
            await redis_db.hset(f"job:{job_id}", "status", "complete")
            # Fix #3: Set a 24-hour TTL so completed job keys don't accumulate
            # in Redis memory indefinitely.
            await redis_db.expire(f"job:{job_id}", 86400)

        except Exception as e:
            logger.error("Background worker failed for job %s: %s", job_id, e)
            await redis_db.hset(f"job:{job_id}", mapping={"status": "failed", "error": str(e)})
            # Fix #3: TTL on the failure state too — failed jobs should not live
            # in Redis forever either.
            await redis_db.expire(f"job:{job_id}", 86400)
        # NOTE: No explicit conn.close() — pool.acquire() context manager returns
        # the connection to the pool automatically on exit.


@router.post("/generate-batch/{tenant_id}")
async def trigger_batch_generation(
    tenant_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    batch_size: int = 10
):
    """Instantly returns a Job ID while processing the batch in the background."""
    # Fix #4: Per-tenant idempotency lock using SET NX EX.
    # SET NX ("set if not exists") is atomic in Redis — only one caller wins.
    # TTL of 60 seconds auto-releases the lock if the worker crashes before
    # run_batch_background can start, preventing a permanently stuck tenant.
    lock_key = f"batch_lock:{tenant_id}"
    lock_acquired = await redis_db.set(lock_key, "1", nx=True, ex=60)

    if not lock_acquired:
        raise HTTPException(
            status_code=409,
            detail="Batch generation already in progress for this tenant. "
                   "Please wait for the current job to complete before submitting a new one."
        )

    job_id = str(uuid.uuid4())

    # Pre-register the job as queued
    await redis_db.hset(f"job:{job_id}", mapping={"status": "queued", "total": batch_size, "completed": 0})

    # Pass the pool from app.state explicitly — the background task runs outside
    # the request context and cannot use the get_db dependency directly.
    pool = request.app.state.db_pool
    background_tasks.add_task(run_batch_background, tenant_id, batch_size, job_id, pool)

    return {
        "status": "accepted",
        "job_id": job_id,
        "message": "Batch processing started in the background."
    }

@router.get("/job-status/{job_id}")
async def get_job_status(job_id: str):
    """Endpoint for the frontend to poll the live progress of a batch job."""
    job_data = await redis_db.hgetall(f"job:{job_id}")
    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found.")
    
    return {
        "job_id": job_id,
        "status": job_data.get("status"),
        "total": int(job_data.get("total", 0)),
        "completed": int(job_data.get("completed", 0)),
        "error": job_data.get("error")
    }

@router.get("/results/{tenant_id}")
async def get_processed_results(tenant_id: int, conn = Depends(get_db)):
    """Fetches completed B2B leads to display on the frontend dashboard."""
    records = await conn.fetch("""
        SELECT company_name, domain, plie_score, headcount_current, funding_stage, intent_score, 
               message_draft_a, message_draft_b, message_draft_c 
        FROM b2b_leads 
        WHERE tenant_id = $1 AND enrichment_status = 'complete'
        ORDER BY plie_score DESC
    """, tenant_id)
    return [dict(r) for r in records]