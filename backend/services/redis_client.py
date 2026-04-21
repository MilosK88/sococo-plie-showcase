import os
import redis.asyncio as redis
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# Connect to the Docker Redis container we mapped to port 6380
REDIS_URL = os.getenv("REDIS_URL", f"redis://127.0.0.1:{os.getenv('REDIS_PORT', 6380)}")
redis_db = redis.from_url(REDIS_URL, decode_responses=True)