from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base

from settings import settings

# Use psycopg v3 driver (sqlalchemy[dialects.postgresql.psycopg])
raw_url = settings.DATABASE_URL
if raw_url.startswith("postgresql://"):
    DATABASE_URL = "postgresql+psycopg://" + raw_url[len("postgresql://") :]
else:
    DATABASE_URL = raw_url

engine = create_engine(DATABASE_URL, future=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session)

Base = declarative_base()


def get_db_session() -> Generator[Session, None, None]:
    """FastAPI dependency: provide a SQLAlchemy session per-request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

