"""Comprehensive End-to-End API Verification Script."""
import os
import sys
import uuid
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///./test_verify.db"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only-32chars"
os.environ["JWT_REFRESH_SECRET_KEY"] = "test-refresh-secret-key-for-testing-only-32chars"
os.environ["LOG_LEVEL"] = "WARNING"

from meeting_notes_agent.api.main import app
from meeting_notes_agent.database.session import Base, get_db
from meeting_notes_agent.database.models import User, UserRole, Meeting, Task, TaskStatus, TaskPriority
from meeting_notes_agent.auth.security import hash_password

def run_verification():
    print("=" * 80)
    print("         MEETING NOTES AGENT API - END-TO-END VERIFICATION")
    print("=" * 80)

    # Setup database
    engine = create_engine(
        "sqlite:///./test_verify.db",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    passed_count = 0
    failed_count = 0

    def assert_test(desc, condition, details=""):
        nonlocal passed_count, failed_count
        if condition:
            passed_count += 1
            print(f"  [OK] {desc}")
        else:
            failed_count += 1
            print(f"  [FAIL] {desc} -> {details}")

    # =========================================================================
    # 1. Health Endpoints
    # =========================================================================
    print("\n[1/7] Testing Health & Liveness Endpoints...")
    res = client.get("/health")
    assert_test("GET /health -> 200 OK & healthy", res.status_code == 200 and res.json().get("status") == "healthy", res.text)

    res = client.get("/health/ready")
    assert_test("GET /health/ready -> 200 OK", res.status_code == 200, res.text)

    res = client.get("/health/live")
    assert_test("GET /health/live -> 200 OK & alive", res.status_code == 200 and res.json().get("status") == "alive", res.text)

    # =========================================================================
    # 2. Authentication & User Management
    # =========================================================================
    print("\n[2/7] Testing Authentication (Register, Login, Token Refresh)...")
    u1_email = f"alice_{uuid.uuid4().hex[:6]}@example.com"
    u2_email = f"bob_{uuid.uuid4().hex[:6]}@example.com"
    admin_email = f"admin_{uuid.uuid4().hex[:6]}@example.com"
    pw = "SecurePass123!"

    # Register User 1
    res = client.post("/api/v1/auth/register", json={"email": u1_email, "password": pw, "full_name": "Alice Johnson"})
    assert_test("POST /api/v1/auth/register (User 1) -> 201 Created", res.status_code == 201 and res.json().get("email") == u1_email, res.text)
    user1_id = res.json().get("id")

    # Duplicate registration
    res = client.post("/api/v1/auth/register", json={"email": u1_email, "password": pw, "full_name": "Duplicate Alice"})
    assert_test("POST /api/v1/auth/register (Duplicate) -> 409 Conflict", res.status_code == 409, res.text)

    # Register User 2
    res = client.post("/api/v1/auth/register", json={"email": u2_email, "password": pw, "full_name": "Bob Smith"})
    assert_test("POST /api/v1/auth/register (User 2) -> 201 Created", res.status_code == 201, res.text)

    # Login User 1
    res = client.post("/api/v1/auth/login", json={"email": u1_email, "password": pw})
    assert_test("POST /api/v1/auth/login (User 1) -> 200 OK with Bearer tokens", res.status_code == 200 and "access_token" in res.json(), res.text)
    u1_tokens = res.json()
    u1_headers = {"Authorization": f"Bearer {u1_tokens['access_token']}"}

    # Login User 2
    res = client.post("/api/v1/auth/login", json={"email": u2_email, "password": pw})
    assert_test("POST /api/v1/auth/login (User 2) -> 200 OK", res.status_code == 200, res.text)
    u2_headers = {"Authorization": f"Bearer {res.json()['access_token']}"}

    # Login Invalid Credentials
    res = client.post("/api/v1/auth/login", json={"email": u1_email, "password": "WrongPassword!"})
    assert_test("POST /api/v1/auth/login (Wrong Password) -> 401 Unauthorized", res.status_code == 401, res.text)

    # Refresh Token
    res = client.post("/api/v1/auth/refresh", json={"refresh_token": u1_tokens["refresh_token"]})
    assert_test("POST /api/v1/auth/refresh (Valid Token) -> 200 OK with new tokens", res.status_code == 200 and "access_token" in res.json(), res.text)

    # Refresh Token with Invalid Token
    res = client.post("/api/v1/auth/refresh", json={"refresh_token": "bad.token.value"})
    assert_test("POST /api/v1/auth/refresh (Invalid Token) -> 401 Unauthorized", res.status_code == 401, res.text)

    # =========================================================================
    # 3. User Profile Operations
    # =========================================================================
    print("\n[3/7] Testing User Profile Endpoints...")
    res = client.get("/api/v1/users/me", headers=u1_headers)
    assert_test("GET /api/v1/users/me -> 200 OK with user details", res.status_code == 200 and res.json().get("email") == u1_email, res.text)

    res = client.patch("/api/v1/users/me", json={"full_name": "Alice J. Expert"}, headers=u1_headers)
    assert_test("PATCH /api/v1/users/me -> 200 OK updated name", res.status_code == 200 and res.json().get("full_name") == "Alice J. Expert", res.text)

    # =========================================================================
    # 4. Meetings Management & Validations
    # =========================================================================
    print("\n[4/7] Testing Meeting Endpoints & Source Validations...")
    # Validation: Missing all sources
    res = client.post("/api/v1/meetings", json={
        "title": "Invalid Meeting",
        "meeting_date": "2026-08-20",
        "attendees": [{"name": "Alice", "email": u1_email}]
    }, headers=u1_headers)
    assert_test("POST /api/v1/meetings (Missing Source) -> 400 Bad Request", res.status_code == 400, res.text)

    # Validation: Multiple sources
    res = client.post("/api/v1/meetings", json={
        "title": "Invalid Meeting",
        "meeting_date": "2026-08-20",
        "transcript_text": "Text content",
        "audio_file_path": "audio.mp3",
        "attendees": [{"name": "Alice", "email": u1_email}]
    }, headers=u1_headers)
    assert_test("POST /api/v1/meetings (Multiple Sources) -> 400 Bad Request", res.status_code == 400, res.text)

    # Valid creation with transcript text
    res = client.post("/api/v1/meetings", json={
        "title": "Q3 Architecture Review",
        "meeting_date": "2026-08-20",
        "meeting_time": "14:00",
        "project_name": "Core Platform",
        "agenda": ["Review API design", "Decide on DB schema"],
        "notes": "Internal tech sync",
        "transcript_text": "Alice: Today we review the new REST API design. Bob: Looks solid, let's ship.",
        "attendees": [
            {"name": "Alice J.", "email": u1_email},
            {"name": "Bob S.", "email": u2_email}
        ]
    }, headers=u1_headers)
    assert_test("POST /api/v1/meetings (Valid creation) -> 201 Created", res.status_code == 201 and "id" in res.json(), res.text)
    meeting_id = res.json().get("id")

    # List meetings
    res = client.get("/api/v1/meetings", headers=u1_headers)
    assert_test("GET /api/v1/meetings -> 200 OK list", res.status_code == 200 and isinstance(res.json(), list) and len(res.json()) >= 1, res.text)

    # Get meeting details
    res = client.get(f"/api/v1/meetings/{meeting_id}", headers=u1_headers)
    assert_test("GET /api/v1/meetings/{id} -> 200 OK with correct ID", res.status_code == 200 and res.json().get("id") == meeting_id, res.text)

    # Update meeting metadata
    res = client.patch(f"/api/v1/meetings/{meeting_id}", json={
        "title": "Q3 Architecture Review - Final",
        "project_name": "Core Platform v2"
    }, headers=u1_headers)
    assert_test("PATCH /api/v1/meetings/{id} -> 200 OK updated title", res.status_code == 200 and res.json().get("title") == "Q3 Architecture Review - Final", res.text)

    # Meeting status
    res = client.get(f"/api/v1/meetings/{meeting_id}/status", headers=u1_headers)
    assert_test("GET /api/v1/meetings/{id}/status -> 200 OK", res.status_code == 200 and "status" in res.json(), res.text)

    # Audio file upload
    res = client.post(
        f"/api/v1/meetings/{meeting_id}/audio",
        files={"file": ("recording.mp3", b"dummy audio mp3 content bytes", "audio/mpeg")},
        headers=u1_headers
    )
    assert_test("POST /api/v1/meetings/{id}/audio -> 200 OK uploaded", res.status_code == 200 and res.json().get("status") == "uploaded", res.text)

    # Transcript file upload
    res = client.post(
        f"/api/v1/meetings/{meeting_id}/transcript",
        files={"file": ("transcript.txt", b"Alice: Meeting notes content.", "text/plain")},
        headers=u1_headers
    )
    assert_test("POST /api/v1/meetings/{id}/transcript -> 200 OK uploaded", res.status_code == 200 and res.json().get("status") == "uploaded", res.text)

    # Meeting results
    res = client.get(f"/api/v1/meetings/{meeting_id}/results", headers=u1_headers)
    assert_test("GET /api/v1/meetings/{id}/results -> 200 OK", res.status_code == 200 and "tasks" in res.json(), res.text)

    # =========================================================================
    # 5. Multi-Tenant Cross-User Isolation
    # =========================================================================
    print("\n[5/7] Testing Multi-Tenant Data Isolation & Security...")
    res = client.get(f"/api/v1/meetings/{meeting_id}", headers=u2_headers)
    assert_test("Security: User 2 cannot GET User 1's meeting -> 404 Not Found", res.status_code == 404, res.text)

    res = client.patch(f"/api/v1/meetings/{meeting_id}", json={"title": "Hacked Title"}, headers=u2_headers)
    assert_test("Security: User 2 cannot PATCH User 1's meeting -> 404 Not Found", res.status_code == 404, res.text)

    res = client.delete(f"/api/v1/meetings/{meeting_id}", headers=u2_headers)
    assert_test("Security: User 2 cannot DELETE User 1's meeting -> 404 Not Found", res.status_code == 404, res.text)

    # =========================================================================
    # 6. Tasks Management
    # =========================================================================
    print("\n[6/7] Testing Task Endpoints...")
    res = client.get("/api/v1/tasks", headers=u1_headers)
    assert_test("GET /api/v1/tasks -> 200 OK task list", res.status_code == 200 and "tasks" in res.json(), res.text)

    res = client.get("/api/v1/tasks?status=todo", headers=u1_headers)
    assert_test("GET /api/v1/tasks?status=todo -> 200 OK filter", res.status_code == 200 and "tasks" in res.json(), res.text)

    fake_uuid = str(uuid.uuid4())
    res = client.get(f"/api/v1/tasks/{fake_uuid}", headers=u1_headers)
    assert_test("GET /api/v1/tasks/{nonexistent_id} -> 404 Not Found", res.status_code == 404, res.text)

    # =========================================================================
    # 7. Role-Based Access Control (Admin Endpoints)
    # =========================================================================
    print("\n[7/7] Testing Role-Based Access Control (Admin vs Regular User)...")
    # Regular user attempting admin endpoints -> 403 Forbidden
    res = client.get("/api/v1/admin/stats", headers=u1_headers)
    assert_test("RBAC: Regular user GET /api/v1/admin/stats -> 403 Forbidden", res.status_code == 403, res.text)

    res = client.get("/api/v1/admin/users", headers=u1_headers)
    assert_test("RBAC: Regular user GET /api/v1/admin/users -> 403 Forbidden", res.status_code == 403, res.text)

    # Create Admin in DB
    db = TestingSessionLocal()
    admin_obj = User(
        email=admin_email,
        password_hash=hash_password(pw),
        full_name="Admin Administrator",
        role=UserRole.ADMIN,
    )
    db.add(admin_obj)
    db.commit()
    db.refresh(admin_obj)
    db.close()

    # Login Admin
    res = client.post("/api/v1/auth/login", json={"email": admin_email, "password": pw})
    admin_headers = {"Authorization": f"Bearer {res.json()['access_token']}"}

    # Admin Stats
    res = client.get("/api/v1/admin/stats", headers=admin_headers)
    assert_test("Admin: GET /api/v1/admin/stats -> 200 OK", res.status_code == 200 and "total_users" in res.json(), res.text)

    # Admin Users
    res = client.get("/api/v1/admin/users", headers=admin_headers)
    assert_test("Admin: GET /api/v1/admin/users -> 200 OK list", res.status_code == 200 and isinstance(res.json(), list) and len(res.json()) >= 3, res.text)

    # Admin Meetings
    res = client.get("/api/v1/admin/meetings", headers=admin_headers)
    assert_test("Admin: GET /api/v1/admin/meetings -> 200 OK list", res.status_code == 200 and isinstance(res.json(), list), res.text)

    # Admin Get User Detail
    res = client.get(f"/api/v1/admin/users/{user1_id}", headers=admin_headers)
    assert_test("Admin: GET /api/v1/admin/users/{id} -> 200 OK", res.status_code == 200 and res.json().get("id") == user1_id, res.text)

    # Admin Adjust Credits
    res = client.post(f"/api/v1/admin/users/{user1_id}/credits?amount=100&reason=MonthlyBonus", headers=admin_headers)
    assert_test("Admin: POST /api/v1/admin/users/{id}/credits -> 200 OK", res.status_code == 200 and "balance" in res.json(), res.text)

    # Admin Adjust Quota
    res = client.post(f"/api/v1/admin/users/{user1_id}/quota?monthly_limit=50", headers=admin_headers)
    assert_test("Admin: POST /api/v1/admin/users/{id}/quota -> 200 OK", res.status_code == 200 and res.json().get("monthly_meeting_limit") == 50, res.text)

    # Cleanup Meeting
    res = client.delete(f"/api/v1/meetings/{meeting_id}", headers=u1_headers)
    assert_test("DELETE /api/v1/meetings/{id} -> 204 No Content", res.status_code == 204, res.text)

    res = client.get(f"/api/v1/meetings/{meeting_id}", headers=u1_headers)
    assert_test("GET /api/v1/meetings/{id} after delete -> 404 Not Found", res.status_code == 404, res.text)

    # =========================================================================
    # SUMMARY
    # =========================================================================
    total = passed_count + failed_count
    print("\n" + "=" * 80)
    print(f"VERIFICATION SUMMARY: {passed_count}/{total} Passed ({(passed_count/total)*100:.1f}%)")
    print("=" * 80)

    try:
        if os.path.exists("test_verify.db"):
            os.remove("test_verify.db")
    except Exception:
        pass

    return 0 if failed_count == 0 else 1

if __name__ == "__main__":
    sys.exit(run_verification())
