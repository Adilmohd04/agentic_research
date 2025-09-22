"""
Integration tests for authentication API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.api.auth import router as auth_router


@pytest.fixture
def app():
    """Create test FastAPI app."""
    app = FastAPI()
    app.include_router(auth_router)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestAuthAPI:
    """Test authentication API endpoints."""
    
    def test_login_success(self, client):
        """Test successful login."""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "admin",
                "password": "admin123!"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["username"] == "admin"
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "admin",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]
    
    def test_login_missing_fields(self, client):
        """Test login with missing fields."""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "admin"
                # Missing password
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_current_user_info_success(self, client):
        """Test getting current user info with valid token."""
        # First login to get token
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": "admin",
                "password": "admin123!"
            }
        )
        
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Get user info
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["username"] == "admin"
        assert data["role"] == "admin"
        assert "permissions" in data
        assert "token_expires" in data
    
    def test_get_current_user_info_invalid_token(self, client):
        """Test getting current user info with invalid token."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        
        assert response.status_code == 401
    
    def test_get_current_user_info_no_token(self, client):
        """Test getting current user info without token."""
        response = client.get("/api/auth/me")
        
        assert response.status_code == 403  # FastAPI returns 403 for missing auth
    
    def test_get_user_permissions(self, client):
        """Test getting user permissions."""
        # First login to get token
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": "admin",
                "password": "admin123!"
            }
        )
        
        token = login_response.json()["access_token"]
        
        # Get permissions
        response = client.get(
            "/api/auth/permissions",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["username"] == "admin"
        assert data["role"] == "admin"
        assert "permissions" in data
        assert len(data["permissions"]) > 0
    
    def test_logout(self, client):
        """Test logout functionality."""
        # First login to get token
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": "admin",
                "password": "admin123!"
            }
        )
        
        token = login_response.json()["access_token"]
        
        # Logout
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert "Successfully logged out" in response.json()["message"]
    
    def test_health_check(self, client):
        """Test authentication service health check."""
        response = client.get("/api/auth/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "authentication"


class TestAuthAPIAdminEndpoints:
    """Test admin-only authentication endpoints."""
    
    def test_get_available_roles_admin(self, client):
        """Test getting available roles as admin."""
        # Login as admin
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": "admin",
                "password": "admin123!"
            }
        )
        
        token = login_response.json()["access_token"]
        
        # Get roles
        response = client.get(
            "/api/auth/roles",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "roles" in data
        assert len(data["roles"]) > 0
        
        # Check that admin role is present
        role_values = [role["value"] for role in data["roles"]]
        assert "admin" in role_values
    
    def test_get_all_permissions_admin(self, client):
        """Test getting all permissions as admin."""
        # Login as admin
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": "admin",
                "password": "admin123!"
            }
        )
        
        token = login_response.json()["access_token"]
        
        # Get permissions
        response = client.get(
            "/api/auth/permissions/all",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "permissions" in data
        assert len(data["permissions"]) > 0
        
        # Check that user_management permission is present
        perm_values = [perm["value"] for perm in data["permissions"]]
        assert "user_management" in perm_values
    
    def test_list_users_admin(self, client):
        """Test listing users as admin."""
        # Login as admin
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": "admin",
                "password": "admin123!"
            }
        )
        
        token = login_response.json()["access_token"]
        
        # List users
        response = client.get(
            "/api/auth/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "users" in data
        assert len(data["users"]) >= 1  # At least the admin user
        
        # Check admin user is present
        usernames = [user["username"] for user in data["users"]]
        assert "admin" in usernames


if __name__ == "__main__":
    pytest.main([__file__])