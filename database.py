from db import engine, Base, get_db_session


async def connect_db():
    """Startup hook: ensure SQLAlchemy tables exist."""
    Base.metadata.create_all(bind=engine)
    print("✓ Database initialized (SQLAlchemy)")


async def disconnect_db():
    """Shutdown hook."""
    print("✓ Database shutdown complete")


def get_db():
    """FastAPI dependency: SQLAlchemy session."""
    yield from get_db_session()
