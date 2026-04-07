import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
import asyncpg
from dotenv import load_dotenv

# 1. LOAD ENVIRONMENT VARIABLES FIRST
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

# 2. NOW IMPORT LOCAL ROUTERS
from api import upload, reactivate

# Global variable to hold our database connection pool
db_pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool
    try:
        # Startup: Create a connection pool to PostgreSQL
        db_pool = await asyncpg.create_pool(
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            database=os.getenv("POSTGRES_DB"),
            host="127.0.0.1",
            port=5432
        )
        print("Database connection pool established.")
        yield
    except Exception as e:
        print(f"CRITICAL ERROR during startup: {e}")
        raise e
    finally:
        # Shutdown: Close the pool cleanly
        if db_pool:
            await db_pool.close()
            print("Database connection pool closed.")

# Initialize the FastAPI application
app = FastAPI(title="LuKul CRE Engine", lifespan=lifespan)

@app.get("/")
async def root():
    return {"status": "ok", "service": "CRE Engine API"}

@app.get("/health/db")
async def db_health():
    """Test endpoint to verify PostgreSQL connectivity."""
    if not db_pool:
        raise HTTPException(status_code=500, detail="Database pool not initialized.")
    
    try:
        async with db_pool.acquire() as connection:
            db_version = await connection.fetchval("SELECT version();")
            return {"status": "connected", "postgres_version": db_version}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

# Register the routers
app.include_router(upload.router, prefix="/api", tags=["Data Ingestion"])
app.include_router(reactivate.router, prefix="/api", tags=["AI Processing"])