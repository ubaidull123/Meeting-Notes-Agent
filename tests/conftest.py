"""Pytest configuration and fixtures."""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment before importing app
test_database_url = os.environ.get("TEST_DATABASE_URL", "sqlite:///./test.db")
sqlalchemy_test_database_url = (
    "postgresql://" + test_database_url.removeprefix("postgres://")
    if test_database_url.startswith("postgres://")
    else test_database_url
)
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = test_database_url
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["LOG_LEVEL"] = "WARNING"
os.environ.setdefault("DATABASE_POOL_SIZE", "2")
os.environ.setdefault("DATABASE_MAX_OVERFLOW", "1")

from meeting_notes_agent.api.main import app
from meeting_notes_agent.database.session import Base, get_db
from meeting_notes_agent.database.models import (
    PlatformRole,
    Team,
    TeamMembership,
    TeamRole,
    User,
    UserRole,
)
from meeting_notes_agent.auth.security import hash_password


def _add_default_team(db_session, user: User, *, name: str) -> Team:
    """Give directly-created fixture users the same workspace as registration."""
    team = Team(name=name, description="Test workspace", created_by=user.id)
    db_session.add(team)
    db_session.flush()
    db_session.add(
        TeamMembership(team_id=team.id, user_id=user.id, role=TeamRole.OWNER)
    )
    db_session.commit()
    db_session.refresh(team)
    return team


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    if sqlalchemy_test_database_url.startswith("sqlite"):
        engine = create_engine(
            sqlalchemy_test_database_url,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )
    else:
        engine = create_engine(
            sqlalchemy_test_database_url,
            pool_pre_ping=True,
            pool_size=2,
            max_overflow=0,
        )
    Base.metadata.create_all(bind=engine)
    yield engine
    if sqlalchemy_test_database_url.startswith("sqlite"):
        Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine):
    """Create a new database session for each test."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session):
    """Create a test user."""
    # Use a unique email for each test run to avoid conflicts
    import uuid
    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"

    user = User(
        email=unique_email,
        password_hash=hash_password("TestPass123!"),
        full_name="Test User",
        role=UserRole.USER,
    )
    db_session.add(user)
    db_session.flush()
    _add_default_team(db_session, user, name="Test User Team")
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def admin_user(db_session):
    """Create an admin user."""
    import uuid
    unique_email = f"admin_{uuid.uuid4().hex[:8]}@example.com"

    user = User(
        email=unique_email,
        password_hash=hash_password("AdminPass123!"),
        full_name="Admin User",
        role=UserRole.ADMIN,
        platform_role=PlatformRole.PLATFORM_ADMIN,
    )
    db_session.add(user)
    db_session.flush()
    _add_default_team(db_session, user, name="Admin User Team")
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(client, test_user):
    """Get authentication headers for test user."""
    response = client.post("/api/v1/auth/login", json={
        "email": test_user.email,
        "password": "TestPass123!"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def admin_headers(client, admin_user):
    """Get authentication headers for admin user."""
    response = client.post("/api/v1/auth/login", json={
        "email": admin_user.email,
        "password": "AdminPass123!"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
