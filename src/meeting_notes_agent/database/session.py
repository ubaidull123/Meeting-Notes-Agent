"""Database session management."""
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, StaticPool

from meeting_notes_agent.config.core.config import settings
from meeting_notes_agent.database.models import Base
# Determine if using SQLite (for testing)
is_sqlite = settings.database_url.startswith("sqlite")

# Create engine with connection pooling
if is_sqlite:
    # SQLite doesn't support QueuePool, use StaticPool for in-memory or file-based
    engine = create_engine(
        settings.database_url,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=settings.debug,
    )
else:
    # PostgreSQL with connection pooling
    engine = create_engine(
        settings.database_url,
        poolclass=QueuePool,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=settings.debug,
    )

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """Get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Verify connectivity without creating, altering, or backfilling schema."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


def close_db() -> None:
    """Close database connections."""
    engine.dispose()
