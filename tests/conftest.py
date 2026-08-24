"""Pytest configuration and fixtures."""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment before importing app
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["LOG_LEVEL"] = "WARNING"

from meeting_notes_agent.api.main import app
from meeting_notes_agent.database.session import Base, get_db
from meeting_notes_agent.database.models import User, UserRole
from meeting_notes_agent.auth.security import hash_password


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    engine = create_engine(
        "sqlite:///./test.db",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


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
    db_session.commit()
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
    )
    db_session.add(user)
    db_session.commit()
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