import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
import asyncpg
from dotenv import load_dotenv

# 1. LOAD ENVIRONMENT VARIABLES FIRST
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

logger = logging.getLogger(__name__)

# 2. NOW IMPORT LOCAL ROUTERS
from api import upload, reactivate

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the asyncpg connection pool for the lifetime of the application.
    The pool is the single source of DB connections — no raw asyncpg.connect()
    calls exist anywhere else in the codebase.
    """
    pool = None
    try:
        pool = await asyncpg.create_pool(
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            database=os.getenv("POSTGRES_DB"),
            host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
            port=int(os.getenv("POSTGRES_PORT", "5433")),  # Matches Docker mapping
            min_size=2,
            max_size=10,
        )
        app.state.db_pool = pool
        logger.info("Database connection pool established (min=2, max=10).")
        yield
    except Exception as e:
        logger.critical("CRITICAL: Failed to establish DB pool during startup: %s", e)
        raise
    finally:
        if pool:
            await pool.close()
            logger.info("Database connection pool closed cleanly.")

# Initialize the FastAPI application
app = FastAPI(title="Sococo PLIE Engine", lifespan=lifespan)


@app.get("/")
async def root(request: Request):
    # Safely check if the pool exists on the app state
    pool = getattr(request.app.state, "db_pool", None)
    return {
        "engine": "Sococo PLIE Showcase",
        "status": "online",
        "db_connected": pool is not None
    }

# Register the routers
app.include_router(upload.router, prefix="/api", tags=["Data Ingestion"])
app.include_router(reactivate.router, prefix="/api", tags=["AI Processing"])