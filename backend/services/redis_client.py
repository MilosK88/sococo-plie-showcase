import os

import redis.asyncio as redis

from dotenv import load_dotenv, find_dotenv



load_dotenv(find_dotenv())



# --- HARDCODED RAILWAY CONNECTION ---

# Bypassing environment variables to force the connection over the public proxy

RAILWAY_URL = "redis://default:KkwCMzbQcjBHnDzADFiOmJBltETjOgHH@shinkansen.proxy.rlwy.net:52410"



redis_db = redis.from_url(RAILWAY_URL, decode_responses=True)