import asyncio
import datetime
from fastapi import APIRouter, HTTPException, Depends
from main import get_db
from services.llm_engine import generate_reactivation_drafts

router = APIRouter()

def calculate_cre_score(churn_date, data_completeness):
    """
    Mathematical scoring engine based on behavioral telemetry.
    Returns a score from 0-100 and a natural language explanation.
    """
    score = 50 # Base score
    
    # Add points for data quality
    score += int(data_completeness * 20)
    
    # Calculate churn age
    months_churned = (datetime.date.today() - churn_date).days / 30
    
    explanation = ""
    if months_churned < 3:
        score += 25
        explanation = "High priority. Churned recently (< 3 months)."
    elif months_churned < 6:
        score += 10
        explanation = "Warm target. Churned 3-6 months ago."
    elif months_churned > 12:
        score -= 20
        explanation = "Cold target. Churned > 1 year ago. Requires strong offer."
    else:
        explanation = "Standard reactivation target."
        
    # Cap score between 0 and 100
    final_score = max(0, min(100, score))
    return final_score, explanation

async def process_single_lead(member_dict: dict):
    """Wrapper function to handle scoring and LLM generation for a single lead."""
    score, explanation = calculate_cre_score(
        member_dict['churn_date'], 
        member_dict['data_completeness']
    )
    
    drafts = await generate_reactivation_drafts(member_dict)
    
    if drafts:
        return {
            "id": member_dict['id'],
            "score": score,
            "explanation": explanation,
            "drafts": drafts
        }
    return None

@router.post("/generate-batch/{tenant_id}")
async def generate_drafts_batch(tenant_id: int, batch_size: int = 10, conn = Depends(get_db)):
    """
    Pulls a batch of unprocessed leads, generates drafts in PARALLEL via OpenAI,
    and bulk updates the database in a single transaction.
    """
    try:
        # Fetch members who do NOT have a draft yet
        members = await conn.fetch("""
            SELECT id, contact_name as first_name, company_name, domain, headcount_current, headcount_growth_pct 
            FROM b2b_leads 
            WHERE tenant_id = $1 AND message_draft_a IS NULL
            LIMIT $2
        """, tenant_id, batch_size)

        if not members:
            return {"status": "complete", "message": "No unprocessed leads left in queue."}

        # 1. Fire all LLM tasks simultaneously (Parallel Execution)
        tasks = [process_single_lead(dict(record)) for record in members]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 2. Filter out failures and format for bulk DB update
        successful_updates = []
        for result in results:
            if isinstance(result, Exception):
                print(f"Parallel processing error: {str(result)}")
                continue
            if result:
                successful_updates.append((
                    result['score'],
                    result['explanation'],
                    result['drafts']['message_draft_a'],
                    result['drafts']['message_draft_b'],
                    result['drafts']['message_draft_c'],
                    result['id']
                ))

        # 3. Bulk update the database in one highly-efficient transaction
        if successful_updates:
            await conn.executemany("""
                UPDATE b2b_leads 
                SET plie_score = $1, 
                    score_explanation = $2,
                    message_draft_a = $3,
                    message_draft_b = $4,
                    message_draft_c = $5,
                    enrichment_status = 'complete'
                WHERE id = $6
            """, successful_updates)
                
        return {
            "status": "success", 
            "message": f"Successfully processed {len(successful_updates)} leads in parallel."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")