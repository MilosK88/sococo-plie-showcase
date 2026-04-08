import os
import asyncpg
from dotenv import load_dotenv, find_dotenv

# Find and load the .env file automatically
load_dotenv(find_dotenv())

async def get_db():
    """Yields a database connection and ensures it closes afterward."""
    conn = await asyncpg.connect(
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB"),
        host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
        port=os.getenv("POSTGRES_PORT", "5433") # Pointing directly to our Docker DB
    )
    try:
        yield conn
    finally:
        await conn.close()

async def get_direct_connection():
    """Opens a standalone database connection for background tasks."""
    return await asyncpg.connect(
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB"),
        host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
        port=os.getenv("POSTGRES_PORT", "5433")
    )