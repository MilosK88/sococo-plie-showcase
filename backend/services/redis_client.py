import os
import redis.asyncio as redis
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# Connect to the Docker Redis container we mapped to port 6380
redis_db = redis.Redis(
    host=os.getenv("REDIS_HOST", "127.0.0.1"),
    port=int(os.getenv("REDIS_PORT", 6380)),
    decode_responses=True # Automatically decodes byte strings to standard Python strings
)