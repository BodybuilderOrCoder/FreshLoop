import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_TTL = int(os.getenv("REC_CACHE_TTL_SECONDS", "3600"))
HALF_LIFE_DAYS = float(os.getenv("REC_HALF_LIFE_DAYS", "30"))
TOP_K = int(os.getenv("REC_TOP_K", "10"))