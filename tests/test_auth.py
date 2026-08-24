"""Tests for authentication endpoints."""
import pytest


class TestAuthEndpoints:
    """Test authentication endpoints."""

    def test_register(self, client):
        """Test user registration."""
        response = client.post("/api/v1/auth/register", json={
            "email": "newuser@example.com",
            "password": "TestPass123!",
            "full_name": "New User"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert "id" in data

    def test_register_duplicate_email(self, client):
        """Test registration with duplicate email fails."""
        # First registration
        client.post("/api/v1/auth/register", json={
            "email": "duplicate@example.com",
            "password": "TestPass123!",
            "full_name": "First User"
        })
        # Second registration with same email
        response = client.post("/api/v1/auth/register", json={
            "email": "duplicate@example.com",
            "password": "TestPass123!",
            "full_name": "Second User"
        })
        assert response.status_code == 409

    def test_login(self, client, test_user):
        """Test user login."""
        response = client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "TestPass123!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_password(self, client, test_user):
        """Test login with invalid password."""
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "WrongPassword"
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user."""
        response = client.post("/api/v1/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "TestPass123!"
        })
        assert response.status_code == 401

    def test_refresh_token(self, client, test_user):
        """Test token refresh."""
        # Login first
        login_response = client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "TestPass123!"
        })
        refresh_token = login_response.json()["refresh_token"]

        # Refresh
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_invalid_token(self, client):
        """Test refresh with invalid token."""
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid-token"
        })
        assert response.status_code == 401


class TestUserProfile:
    """Test user profile endpoints."""

    def test_get_profile(self, client, auth_headers, test_user):
        """Test getting user profile."""
        response = client.get("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["full_name"] == "Test User"
        assert "quota" in data
        assert "credits" in data

    def test_update_profile(self, client, auth_headers, test_user):
        """Test updating user profile."""
        response = client.patch("/api/v1/users/me", json={
            "full_name": "Updated Name"
        }, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"

    def test_change_password(self, client, test_user):
        """Test changing password."""
        # Login first to get headers
        login_response = client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "TestPass123!"
        })
        headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

        response = client.post("/api/v1/users/me/password", json={
            "current_password": "TestPass123!",
            "new_password": "NewPass123!"
        }, headers=headers)
        assert response.status_code == 204

        # Verify new password works
        login_response = client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "NewPass123!"
        })
        assert login_response.status_code == 200

    def test_change_password_wrong_current(self, client, auth_headers):
        """Test changing password with wrong current password."""
        response = client.post("/api/v1/users/me/password", json={
            "current_password": "WrongPassword",
            "new_password": "NewPass123!"
        }, headers=auth_headers)
        assert response.status_code == 400


class TestProtectedEndpoints:
    """Test that protected endpoints require authentication."""

    def test_profile_requires_auth(self, client):
        """Test profile endpoint requires auth."""
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401

    def test_meetings_requires_auth(self, client):
        """Test meetings endpoint requires auth."""
        response = client.get("/api/v1/meetings")
        assert response.status_code == 401

    def test_tasks_requires_auth(self, client):
        """Test tasks endpoint requires auth."""
        response = client.get("/api/v1/tasks")
        assert response.status_code == 401