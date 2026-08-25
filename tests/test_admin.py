"""Tests for admin endpoints."""
import pytest


class TestAdminEndpoints:
    """Test admin endpoints."""

    def test_admin_stats(self, client, admin_headers):
        """Test admin stats endpoint."""
        response = client.get("/api/v1/admin/stats", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "active_users" in data
        assert "total_meetings" in data
        assert "total_tokens_used" in data

    def test_admin_list_users(self, client, admin_headers):
        """Test admin user listing."""
        response = client.get("/api/v1/users", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_admin_list_users_pagination(self, client, admin_headers):
        """Test admin user listing with pagination."""
        response = client.get("/api/v1/users?page=1&page_size=5", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_admin_list_users_filter_by_role(self, client, admin_headers):
        """Test admin user listing filtered by role."""
        response = client.get("/api/v1/users?role=ADMIN", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_admin_list_users_filter_by_active(self, client, admin_headers):
        """Test admin user listing filtered by active status."""
        response = client.get("/api/v1/users?is_active=true", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_admin_get_user(self, client, admin_headers, admin_user):
        """Test getting user detail as admin."""
        response = client.get(f"/api/v1/users/{admin_user.id}", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == admin_user.id
        assert "email" in data
        assert "quota" in data
        assert "credits" in data

    def test_admin_get_nonexistent_user(self, client, admin_headers):
        """Test getting nonexistent user."""
        response = client.get("/api/v1/users/99999", headers=admin_headers)
        assert response.status_code == 404

    def test_admin_update_user(self, client, admin_headers, admin_user):
        """Test updating user as admin."""
        response = client.patch(f"/api/v1/users/{admin_user.id}", json={
            "full_name": "Updated Admin Name"
        }, headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Admin Name"

    def test_admin_adjust_credits(self, client, admin_headers, admin_user):
        """Test adjusting user credits as admin."""
        response = client.post(f"/api/v1/users/{admin_user.id}/credits", params={
            "amount": 100,
            "reason": "Test credit adjustment"
        }, headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "balance" in data

    def test_admin_adjust_quota(self, client, admin_headers, admin_user):
        """Test adjusting user quota as admin."""
        response = client.post(f"/api/v1/users/{admin_user.id}/quota", params={
            "monthly_limit": 50
        }, headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["monthly_meeting_limit"] == 50

    def test_admin_can_delete_other_user(self, client, admin_headers, test_user, db_session):
        """Test admin can remove another user."""
        user_id = test_user.id
        response = client.delete(f"/api/v1/admin/users/{user_id}", headers=admin_headers)
        assert response.status_code == 204
        db_session.expire_all()
        from meeting_notes_agent.database.models import User
        disabled_user = db_session.query(User).filter(User.id == user_id).one()
        assert disabled_user.is_active is False

    def test_admin_cannot_delete_self(self, client, admin_headers, admin_user):
        """Test admin cannot remove their own account."""
        response = client.delete(f"/api/v1/admin/users/{admin_user.id}", headers=admin_headers)
        assert response.status_code == 400
        assert "own admin account" in response.json()["detail"]


class TestAdminRbac:
    """Test RBAC enforcement for admin endpoints."""

    def test_regular_user_cannot_access_admin_stats(self, client, auth_headers):
        """Test regular user cannot access admin stats."""
        response = client.get("/api/v1/admin/stats", headers=auth_headers)
        assert response.status_code == 403

    def test_regular_user_cannot_list_users(self, client, auth_headers):
        """Test regular user cannot list all users."""
        response = client.get("/api/v1/users", headers=auth_headers)
        assert response.status_code == 403

    def test_regular_user_cannot_get_user(self, client, auth_headers, test_user):
        """Test regular user cannot get user detail."""
        response = client.get(f"/api/v1/users/{test_user.id}", headers=auth_headers)
        assert response.status_code == 403

    def test_regular_user_cannot_update_user(self, client, auth_headers, test_user):
        """Test regular user cannot update user."""
        response = client.patch(f"/api/v1/users/{test_user.id}", json={
            "full_name": "Hacked"
        }, headers=auth_headers)
        assert response.status_code == 403

    def test_regular_user_cannot_delete_user(self, client, auth_headers, test_user):
        """Test regular user cannot delete user."""
        response = client.delete(f"/api/v1/users/{test_user.id}", headers=auth_headers)
        assert response.status_code == 403

    def test_regular_user_cannot_adjust_credits(self, client, auth_headers, test_user):
        """Test regular user cannot adjust credits."""
        response = client.post(f"/api/v1/users/{test_user.id}/credits", params={
            "amount": 100,
            "reason": "Hack attempt"
        }, headers=auth_headers)
        assert response.status_code == 403

    def test_regular_user_cannot_adjust_quota(self, client, auth_headers, test_user):
        """Test regular user cannot adjust quota."""
        response = client.post(f"/api/v1/users/{test_user.id}/quota", params={
            "monthly_limit": 50
        }, headers=auth_headers)
        assert response.status_code == 403


class TestAdminMeetings:
    """Test admin meeting management."""

    def test_admin_list_all_meetings(self, client, admin_headers):
        """Test admin listing all meetings."""
        response = client.get("/api/v1/admin/meetings", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_admin_get_meeting_status(self, client, admin_headers):
        """Test admin getting meeting status."""
        from uuid import uuid4
        # Use a meeting ID that might exist
        fake_id = uuid4()
        response = client.get(f"/api/v1/admin/meetings/{fake_id}/status", headers=admin_headers)
        # Might be 404 if not found, but not 403
        assert response.status_code in [200, 404]


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_health_check(self, client):
        """Test basic health check."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "meeting-notes-api"

    def test_readiness_check(self, client):
        """Test readiness check."""
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["ready", "not_ready"]
        assert "database" in data

    def test_liveness_check(self, client):
        """Test liveness check."""
        response = client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
