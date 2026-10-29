"""Configuration for the FreshLoop recommender."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

CACHE_TTL = int(os.getenv("REC_CACHE_TTL_SECONDS", "3600"))
HALF_LIFE_DAYS = float(os.getenv("REC_HALF_LIFE_DAYS", "30"))
TOP_K = int(os.getenv("REC_TOP_K", "10"))

# Keep the existing baseline as the default algorithm.
REC_MODEL = os.getenv("REC_MODEL", "baseline").strip().lower()

# Resolve the default path independently of the current working directory.
_DEFAULT_TRAIN_PATH = (
    Path(__file__).resolve().parents[1]
    / "database"
    / "data"
    / "train_interactions.csv"
)

TRAIN_INTERACTIONS_PATH = os.getenv(
    "REC_TRAIN_INTERACTIONS_PATH",
    str(_DEFAULT_TRAIN_PATH),
)

POOL_SIZE = int(os.getenv("REC_POOL_SIZE", "30"))