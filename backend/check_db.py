import asyncio
import asyncpg
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

async def check_db():
    conn = await asyncpg.connect(
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB"),
        host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
        port=os.getenv("POSTGRES_PORT", "5433")
    )
    
    # We are now selecting ALL THREE drafts
    leads = await conn.fetch("""
        SELECT company_name, domain, plie_score, headcount_current, funding_stage, 
               message_draft_a, message_draft_b, message_draft_c 
        FROM b2b_leads
    """)
    
    for lead in leads:
        print(f"\n{'='*60}")
        print(f"🏢 COMPANY: {lead['company_name']} ({lead['domain']})")
        print(f"📊 PLIE SCORE: {lead['plie_score']}")
        print(f"👥 HEADCOUNT: {lead['headcount_current']} | 💰 FUNDING: {lead['funding_stage']}")
        
        print(f"\n[VARIANT A - The 'Why Now' Trigger]")
        print(f"{lead['message_draft_a']}")
        
        print(f"\n[VARIANT B - The Pattern Interrupt]")
        print(f"{lead['message_draft_b']}")
        
        print(f"\n[VARIANT C - Financial/Ops Blunt Force]")
        print(f"{lead['message_draft_c']}")
        
    await conn.close()

if __name__ == "__main__":
    asyncio.run(check_db())