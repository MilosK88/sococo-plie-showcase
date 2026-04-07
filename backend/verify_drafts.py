import os
import asyncio
import asyncpg
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path=os.path.join(os.path.dirname(BASE_DIR), ".env"))

async def read_drafts():
    try:
        conn = await asyncpg.connect(
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            database=os.getenv("POSTGRES_DB"),
            host="127.0.0.1",
            port=5432
        )
        
        # Fetch the 10 members we just processed
        records = await conn.fetch("""
            SELECT first_name, cre_score, score_explanation, message_draft_a, message_draft_b, message_draft_c 
            FROM churned_members 
            WHERE message_draft_a IS NOT NULL
            LIMIT 3
        """)
        
        print("\n--- INGESTED DRAFTS VERIFICATION ---\n")
        for record in records:
            print(f"TARGET: {record['first_name']} (Score: {record['cre_score']})")
            print(f"CONTEXT: {record['score_explanation']}")
            print(f"VARIANT A: {record['message_draft_a']}")
            print(f"VARIANT B: {record['message_draft_b']}")
            print(f"VARIANT C: {record['message_draft_c']}")
            print("-" * 50)
            
        await conn.close()
    except Exception as e:
        print(f"Failed to read database: {e}")

if __name__ == "__main__":
    asyncio.run(read_drafts())