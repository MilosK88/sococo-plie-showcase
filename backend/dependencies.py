from fastapi import Request


async def get_db(request: Request):
    """
    FastAPI dependency that acquires a connection from the application-level
    asyncpg pool. The pool is initialized at startup (lifespan) and lives on
    app.state — this function is the single, canonical entry point for all
    route-level database access.
    """
    async with request.app.state.db_pool.acquire() as connection:
        yield connection
