import asyncio
import asyncpg
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

async def reset_db():
    conn = await asyncpg.connect(
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB"),
        host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
        port=os.getenv("POSTGRES_PORT", "5433")
    )
    
    # Wipe the AI drafts and reset the status back to pending
    await conn.execute("""
        UPDATE b2b_leads 
        SET message_draft_a = NULL, 
            message_draft_b = NULL, 
            message_draft_c = NULL, 
            enrichment_status = 'pending'
    """)
    
    print("Success! All leads have been reset. You can trigger the batch again.")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(reset_db())