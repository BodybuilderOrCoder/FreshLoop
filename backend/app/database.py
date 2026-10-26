import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# Project root: the directory containing .env and docker-compose.yml.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Load local configuration without overriding environment variables
# already supplied by the operating system or deployment environment.
load_dotenv(PROJECT_ROOT / ".env")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://freshloop_user:freshloop_password123@localhost:5432/freshloop_db",
)

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()