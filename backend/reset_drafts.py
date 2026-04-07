import os
import asyncio
import asyncpg
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path=os.path.join(os.path.dirname(BASE_DIR), ".env"))

async def reset_db_drafts():
    print("Povezivanje sa bazom radi resetovanja...")
    try:
        conn = await asyncpg.connect(
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            database=os.getenv("POSTGRES_DB"),
            host="127.0.0.1",
            port=5432
        )
        
        # Brišemo generisane poruke i skorove samo onima koji ih imaju
        status = await conn.execute("""
            UPDATE churned_members 
            SET message_draft_a = NULL, 
                message_draft_b = NULL, 
                message_draft_c = NULL,
                cre_score = NULL,
                score_explanation = NULL
            WHERE message_draft_a IS NOT NULL
        """)
        
        print(f"Uspesno obrisano! Status operacije: {status}")
        await conn.close()
        
    except Exception as e:
        print(f"Greska pri konekciji: {e}")

if __name__ == "__main__":
    asyncio.run(reset_db_drafts())