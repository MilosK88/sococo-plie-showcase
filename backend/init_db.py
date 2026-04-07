import asyncio
import asyncpg
import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

async def init_db():
    print("Connecting to the database to initialize B2B schema...")
    try:
        conn = await asyncpg.connect(
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            database=os.getenv("POSTGRES_DB"),
            host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
            port=os.getenv("POSTGRES_PORT", "5432")
        )

        # 1. Drop old B2C tables if they exist
        await conn.execute("DROP TABLE IF EXISTS churned_members CASCADE;")
        
        # 2. Create the Tenant table (unchanged, but necessary for isolation)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS gym_tenants (
                id SERIAL PRIMARY KEY,
                tenant_name VARCHAR(255) NOT NULL,
                language_locale VARCHAR(10) DEFAULT 'en',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Seed a test tenant for our Sococo showcase
        await conn.execute("""
            INSERT INTO gym_tenants (id, tenant_name, language_locale) 
            VALUES (1, 'Sococo Showcase', 'en')
            ON CONFLICT (id) DO NOTHING;
        """)

        # 3. Create the new Canonical Lead Object table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS b2b_leads (
                id SERIAL PRIMARY KEY,
                tenant_id INTEGER REFERENCES gym_tenants(id) ON DELETE CASCADE,
                
                -- Core Identity
                company_name VARCHAR(255) NOT NULL,
                contact_name VARCHAR(255) NOT NULL,
                domain VARCHAR(255) NOT NULL,
                
                -- Pipeline State
                enrichment_status VARCHAR(50) DEFAULT 'pending',
                plie_score INTEGER DEFAULT NULL,
                score_explanation TEXT,
                
                -- Raw Firmographics (Populated by Mock APIs later)
                headcount_current INTEGER,
                headcount_growth_pct FLOAT,
                funding_stage VARCHAR(100),
                tech_stack TEXT,
                intent_score INTEGER,
                
                -- AI Outputs
                message_draft_a TEXT,
                message_draft_b TEXT,
                message_draft_c TEXT,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(tenant_id, domain) -- Prevent duplicate companies per tenant
            )
        """)

        print("Success! B2B schema created.")
        await conn.close()
        
    except Exception as e:
        print(f"Database initialization failed: {e}")

if __name__ == "__main__":
    asyncio.run(init_db())