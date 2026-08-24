"""Configuration compatibility tests."""

from meeting_notes_agent.config.core.config import Settings


def test_heroku_postgres_url_is_normalized_for_sqlalchemy() -> None:
    settings = Settings(
        DATABASE_URL="postgres://user:password@example.test/database",
        JWT_SECRET_KEY="test-access-secret",
        JWT_REFRESH_SECRET_KEY="test-refresh-secret",
    )

    assert settings.database_url == (
        "postgresql://user:password@example.test/database"
    )


def test_sqlite_url_is_preserved() -> None:
    settings = Settings(
        DATABASE_URL="sqlite:///./test.db",
        JWT_SECRET_KEY="test-access-secret",
        JWT_REFRESH_SECRET_KEY="test-refresh-secret",
    )

    assert settings.database_url == "sqlite:///./test.db"


def test_postgres_pool_defaults_fit_low_connection_environments(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_POOL_SIZE", raising=False)
    monkeypatch.delenv("DATABASE_MAX_OVERFLOW", raising=False)
    settings = Settings(
        DATABASE_URL="postgresql://user:password@example.test/database",
        JWT_SECRET_KEY="test-access-secret",
        JWT_REFRESH_SECRET_KEY="test-refresh-secret",
    )

    assert settings.database_pool_size == 3
    assert settings.database_max_overflow == 2
