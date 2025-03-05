"""Tests for session management."""

from unittest.mock import AsyncMock, MagicMock, patch
import uuid

import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from app.api.v1.dependencies import get_current_user
from app.core.security import setup_security

# Test data
TEST_TOKEN = "test_token"
TEST_USER_ID = str(uuid.uuid4())
TEST_USER_DATA = {
    "id": TEST_USER_ID,
    "email": "test@example.com",
    "profile": {"id": TEST_USER_ID, "username": "Test User", "bio": "Test bio"},
}


@pytest.fixture
def mock_supabase_service():
    """Mock Supabase service."""
    with patch("app.api.v1.dependencies.get_supabase_service") as mock:
        service = MagicMock()
        service.verify_token = AsyncMock()
        mock.return_value = service
        yield service


@pytest.fixture
def test_app(mock_supabase_service):
    """Create test FastAPI application with test routes."""
    app = FastAPI()
    setup_security(app)

    @app.get("/test/protected")
    async def protected_route(user=Depends(get_current_user)):
        return {"user": user}

    return app


@pytest.fixture
def test_client(test_app):
    """Create test client."""
    return TestClient(test_app)


class TestSessionManagement:
    """Test suite for session management."""

    def test_protected_route_with_valid_token(self, test_client, mock_supabase_service):
        """Test accessing protected route with valid token."""
        # Mock successful token verification
        mock_supabase_service.verify_token.return_value = TEST_USER_DATA

        response = test_client.get(
            "/test/protected", headers={"Authorization": f"Bearer {TEST_TOKEN}"}
        )

        assert response.status_code == 200
        assert response.json()["user"] == TEST_USER_DATA
        mock_supabase_service.verify_token.assert_called_once_with(TEST_TOKEN)

    def test_protected_route_without_token(self, test_client):
        """Test accessing protected route without token."""
        response = test_client.get("/test/protected")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    def test_protected_route_with_invalid_token(self, test_client, mock_supabase_service):
        """Test accessing protected route with invalid token."""
        # Mock failed token verification
        mock_supabase_service.verify_token.return_value = None

        response = test_client.get(
            "/test/protected", headers={"Authorization": f"Bearer {TEST_TOKEN}"}
        )

        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]

    def test_optional_auth_route_with_token(self, test_client, mock_supabase_service):
        """Test accessing route with optional auth using valid token."""
        # Mock successful token verification
        mock_supabase_service.verify_token.return_value = TEST_USER_DATA

        response = test_client.get(
            "/test/optional", headers={"Authorization": f"Bearer {TEST_TOKEN}"}
        )

        assert response.status_code == 200
        assert response.json()["user"] == TEST_USER_DATA

    def test_optional_auth_route_without_token(self, test_client):
        """Test accessing route with optional auth without token."""
        response = test_client.get("/test/optional")
        assert response.status_code == 200
        assert response.json()["user"] is None

    def test_profile_required_route_with_profile(self, test_client, mock_supabase_service):
        """Test accessing profile-required route with valid profile."""
        # Mock successful token verification with profile
        mock_supabase_service.verify_token.return_value = TEST_USER_DATA

        response = test_client.get(
            "/test/profile-required", headers={"Authorization": f"Bearer {TEST_TOKEN}"}
        )

        assert response.status_code == 200
        assert response.json()["user"] == TEST_USER_DATA

    def test_profile_required_route_without_profile(self, test_client, mock_supabase_service):
        """Test accessing profile-required route without profile."""
        # Mock successful token verification but without profile
        user_data_without_profile = {**TEST_USER_DATA, "profile": None}
        mock_supabase_service.verify_token.return_value = user_data_without_profile

        response = test_client.get(
            "/test/profile-required", headers={"Authorization": f"Bearer {TEST_TOKEN}"}
        )

        assert response.status_code == 400
        assert "User profile not found" in response.json()["detail"]
