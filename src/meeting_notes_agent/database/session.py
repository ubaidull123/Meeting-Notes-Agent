"""Database session management."""
from typing import Generator
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, StaticPool

from meeting_notes_agent.core.config import settings
from meeting_notes_agent.database.models import Base, User, UserCredits, UserQuota


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
        pool_size=10,
        max_overflow=20,
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
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
    # Lightweight migration for databases created before credit charging was
    # made idempotent. SQLAlchemy's create_all does not alter existing tables.
    with engine.begin() as connection:
        if engine.dialect.name == "postgresql":
            connection.execute(text(
                "ALTER TABLE meetings ADD COLUMN IF NOT EXISTS credits_charged BOOLEAN NOT NULL DEFAULT FALSE"
            ))
        elif engine.dialect.name == "sqlite":
            columns = connection.execute(text("PRAGMA table_info(meetings)")).fetchall()
            if "credits_charged" not in {column[1] for column in columns}:
                connection.execute(text(
                    "ALTER TABLE meetings ADD COLUMN credits_charged BOOLEAN NOT NULL DEFAULT 0"
                ))

    # Accounts created before billing was introduced may not have related
    # quota/credit rows. Create them once during startup so profile and admin
    # screens show real balances instead of empty values.
    db = SessionLocal()
    try:
        for user_id, in db.query(User.id).all():
            quota = db.query(UserQuota).filter(UserQuota.user_id == user_id).first()
            if quota is None:
                quota = UserQuota(user_id=user_id)
                db.add(quota)
                db.flush()
            if not db.query(UserCredits).filter(UserCredits.user_id == user_id).first():
                db.add(UserCredits(user_id=user_id, balance=quota.monthly_credits))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def close_db() -> None:
    """Close database connections."""
    engine.dispose()
