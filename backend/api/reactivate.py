# backend/api/reactivate.py
import os
import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
import asyncpg
from services.llm_engine import generate_reactivation_drafts

router = APIRouter()

async def get_db_connection():
    return await asyncpg.connect(
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB"),
        host="127.0.0.1",
        port=5432
    )

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

@router.post("/generate-batch/{tenant_id}")
async def generate_drafts_batch(tenant_id: int, batch_size: int = 10):
    """
    Pulls a batch of unprocessed members, generates their drafts via OpenAI,
    and updates the database.
    """
    conn = await get_db_connection()
    try:
        # Fetch members who do NOT have a draft yet
        members = await conn.fetch("""
            SELECT id, first_name, churn_date, preferred_zone, data_completeness 
            FROM churned_members 
            WHERE tenant_id = $1 AND message_draft_a IS NULL
            LIMIT $2
        """, tenant_id, batch_size)

        if not members:
            return {"status": "complete", "message": "No unprocessed members left in queue."}

        processed_count = 0
        
        for record in members:
            member_dict = dict(record)
            
            # 1. Calculate Score
            score, explanation = calculate_cre_score(
                member_dict['churn_date'], 
                member_dict['data_completeness']
            )
            
            # 2. Call OpenAI (Strict Ekavica constraints applied in service layer)
            drafts = await generate_reactivation_drafts(member_dict)
            
            if drafts:
                # 3. Update the database with the AI drafts and calculated score
                await conn.execute("""
                    UPDATE churned_members 
                    SET cre_score = $1, 
                        score_explanation = $2,
                        message_draft_a = $3,
                        message_draft_b = $4,
                        message_draft_c = $5
                    WHERE id = $6
                """, 
                score, 
                explanation, 
                drafts['message_draft_a'], 
                drafts['message_draft_b'], 
                drafts['message_draft_c'], 
                record['id'])
                
                processed_count += 1
                
        return {
            "status": "success", 
            "message": f"Successfully scored and generated drafts for {processed_count} members."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")
    finally:
        await conn.close()