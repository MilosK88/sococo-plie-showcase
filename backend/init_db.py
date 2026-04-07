# backend/init_db.py
import os
import asyncio
import asyncpg
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Load the .env file from the root directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(BASE_DIR), ".env"))

async def initialize_database():
    print("Connecting to database to build schema...")
    try:
        # Establish a single connection (no pool needed for a one-off script)
        conn = await asyncpg.connect(
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            database=os.getenv("POSTGRES_DB"),
            host="127.0.0.1",
            port=5432
        )
        
        # Read the SQL file
        schema_path = os.path.join(BASE_DIR, "core", "schema.sql")
        with open(schema_path, "r") as file:
            sql_commands = file.read()
            
        # Execute the SQL
        await conn.execute(sql_commands)
        
        # Insert a dummy gym tenant so we have an ID to attach our first CSV to
        await conn.execute("""
            INSERT INTO gym_tenants (name, language_locale) 
            VALUES ('Infinity Fitness Academy', 'sr_RS')
            ON CONFLICT DO NOTHING;
        """)
        
        print("Schema successfully built! 'Infinity Fitness Academy' tenant created.")
        await conn.close()
        
    except Exception as e:
        print(f"Failed to initialize database: {e}")

if __name__ == "__main__":
    asyncio.run(initialize_database())