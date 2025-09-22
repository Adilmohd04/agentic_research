"""
Unit tests for authentication and authorization system.
"""

import pytest
from datetime import datetime, timedelta
from fastapi import HTTPException
from unittest.mock import Mock, patch

from src.security.auth import (
    AuthenticationService,
    UserManager,
    TokenManager,
    PasswordManager,
    RolePermissionManager,
    SecurityConfig,
    User,
    UserRole,
    Permission,
    LoginRequest,
    TokenData
)


class TestPasswordManager:
    """Test password management functionality."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "test123!"
        hashed = PasswordManager.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert PasswordManager.verify_password(password, hashed)
    
    def test_verify_password_success(self):
        """Test successful password verification."""
        password = "test123!"
        hashed = PasswordManager.hash_password(password)
        
        assert PasswordManager.verify_password(password, hashed)
    
    def test_verify_password_failure(self):
        """Test failed password verification."""
        password = "test123!"
        wrong_password = "wrong123!"
        hashed = PasswordManager.hash_password(password)
        
        assert not PasswordManager.verify_password(wrong_password, hashed)
    
    def test_validate_password_strength_success(self):
        """Test successful password strength validation."""
        config = SecurityConfig()
        password = "StrongPass123!"
        
        issues = PasswordManager.validate_password_strength(password, config)
        assert len(issues) == 0
    
    def test_validate_password_strength_too_short(self):
        """Test password too short validation."""
        config = SecurityConfig()
        password = "Short1!"
        
        issues = PasswordManager.validate_password_strength(password, config)
        assert any("at least" in issue for issue in issues)
    
    def test_validate_password_strength_missing_complexity(self):
        """Test password missing complexity requirements."""
        config = SecurityConfig()
        password = "lowercase123"  # Missing uppercase and special char
        
        issues = PasswordManager.validate_password_strength(password, config)
        assert len(issues) > 0
        assert any("uppercase" in issue for issue in issues)
        assert any("special character" in issue for issue in issues)


class TestRolePermissionManager:
    """Test role and permission management."""
    
    def test_get_role_permissions(self):
        """Test getting permissions for a role."""
        manager = RolePermissionManager()
        
        admin_perms = manager.get_role_permissions(UserRole.ADMIN)
        viewer_perms = manager.get_role_permissions(UserRole.VIEWER)
        
        assert len(admin_perms) > len(viewer_perms)
        assert Permission.USER_MANAGEMENT in admin_perms
        assert Permission.USER_MANAGEMENT not in viewer_perms
        assert Permission.READ_DOCUMENTS in viewer_perms
    
    def test_has_permission(self):
        """Test permission checking."""
        manager = RolePermissionManager()
        
        assert manager.has_permission(UserRole.ADMIN, Permission.USER_MANAGEMENT)
        assert not manager.has_permission(UserRole.VIEWER, Permission.USER_MANAGEMENT)
        assert manager.has_permission(UserRole.VIEWER, Permission.READ_DOCUMENTS)


class TestTokenManager:
    """Test JWT token management."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        config = SecurityConfig()
        manager = TokenManager(config)
        
        user = User(
            user_id="test-001",
            username="testuser",
            email="test@example.com",
            password_hash="hashed",
            role=UserRole.VIEWER,
            permissions={Permission.READ_DOCUMENTS}
        )
        
        token = manager.create_access_token(user)
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_token_success(self):
        """Test successful token verification."""
        config = SecurityConfig()
        manager = TokenManager(config)
        
        user = User(
            user_id="test-001",
            username="testuser",
            email="test@example.com",
            password_hash="hashed",
            role=UserRole.VIEWER,
            permissions={Permission.READ_DOCUMENTS}
        )
        
        token = manager.create_access_token(user)
        token_data = manager.verify_token(token)
        
        assert token_data.user_id == user.user_id
        assert token_data.username == user.username
        assert token_data.role == user.role.value
    
    def test_verify_token_invalid(self):
        """Test invalid token verification."""
        config = SecurityConfig()
        manager = TokenManager(config)
        
        with pytest.raises(HTTPException) as exc_info:
            manager.verify_token("invalid.token.here")
        
        assert exc_info.value.status_code == 401
    
    def test_verify_token_revoked(self):
        """Test revoked token verification."""
        config = SecurityConfig()
        manager = TokenManager(config)
        
        user = User(
            user_id="test-001",
            username="testuser",
            email="test@example.com",
            password_hash="hashed",
            role=UserRole.VIEWER,
            permissions={Permission.READ_DOCUMENTS}
        )
        
        token = manager.create_access_token(user)
        token_data = manager.verify_token(token)
        
        # Revoke token
        manager.revoked_tokens.add(token_data.jti)
        
        with pytest.raises(HTTPException) as exc_info:
            manager.verify_token(token)
        
        assert exc_info.value.status_code == 401
        assert "revoked" in exc_info.value.detail


class TestUserManager:
    """Test user management functionality."""
    
    def test_create_user_success(self):
        """Test successful user creation."""
        config = SecurityConfig()
        manager = UserManager(config)
        
        user = manager.create_user(
            username="newuser",
            email="newuser@example.com",
            password="StrongPass123!",
            role=UserRole.VIEWER
        )
        
        assert user.username == "newuser"
        assert user.email == "newuser@example.com"
        assert user.role == UserRole.VIEWER
        assert user.is_active
        assert Permission.READ_DOCUMENTS in user.permissions
    
    def test_create_user_duplicate_username(self):
        """Test user creation with duplicate username."""
        config = SecurityConfig()
        manager = UserManager(config)
        
        # First user should succeed
        manager.create_user(
            username="testuser",
            email="test1@example.com",
            password="StrongPass123!",
            role=UserRole.VIEWER
        )
        
        # Second user with same username should fail
        with pytest.raises(ValueError) as exc_info:
            manager.create_user(
                username="testuser",
                email="test2@example.com",
                password="StrongPass123!",
                role=UserRole.VIEWER
            )
        
        assert "already exists" in str(exc_info.value)
    
    def test_create_user_weak_password(self):
        """Test user creation with weak password."""
        config = SecurityConfig()
        manager = UserManager(config)
        
        with pytest.raises(ValueError) as exc_info:
            manager.create_user(
                username="testuser",
                email="test@example.com",
                password="weak",
                role=UserRole.VIEWER
            )
        
        assert "Password validation failed" in str(exc_info.value)
    
    def test_authenticate_user_success(self):
        """Test successful user authentication."""
        config = SecurityConfig()
        manager = UserManager(config)
        
        # Use the default admin user
        user = manager.authenticate_user("admin", "admin123!")
        
        assert user is not None
        assert user.username == "admin"
        assert user.role == UserRole.ADMIN
    
    def test_authenticate_user_wrong_password(self):
        """Test authentication with wrong password."""
        config = SecurityConfig()
        manager = UserManager(config)
        
        user = manager.authenticate_user("admin", "wrongpassword")
        assert user is None
    
    def test_authenticate_user_nonexistent(self):
        """Test authentication with nonexistent user."""
        config = SecurityConfig()
        manager = UserManager(config)
        
        user = manager.authenticate_user("nonexistent", "password")
        assert user is None
    
    def test_authenticate_user_account_locked(self):
        """Test authentication with locked account."""
        config = SecurityConfig()
        manager = UserManager(config)
        
        # Get admin user and lock it
        admin_user = manager.users["admin-001"]
        admin_user.locked_until = datetime.utcnow() + timedelta(minutes=30)
        
        with pytest.raises(HTTPException) as exc_info:
            manager.authenticate_user("admin", "admin123!")
        
        assert exc_info.value.status_code == 423
        assert "locked" in exc_info.value.detail
    
    def test_authenticate_user_inactive(self):
        """Test authentication with inactive account."""
        config = SecurityConfig()
        manager = UserManager(config)
        
        # Get admin user and deactivate it
        admin_user = manager.users["admin-001"]
        admin_user.is_active = False
        
        with pytest.raises(HTTPException) as exc_info:
            manager.authenticate_user("admin", "admin123!")
        
        assert exc_info.value.status_code == 403
        assert "disabled" in exc_info.value.detail
    
    def test_update_user_role(self):
        """Test updating user role."""
        config = SecurityConfig()
        manager = UserManager(config)
        
        # Create a test user
        user = manager.create_user(
            username="testuser",
            email="test@example.com",
            password="StrongPass123!",
            role=UserRole.VIEWER
        )
        
        # Update role
        success = manager.update_user_role(user.user_id, UserRole.RESEARCHER)
        
        assert success
        assert user.role == UserRole.RESEARCHER
        assert Permission.USE_AGENTS in user.permissions
    
    def test_deactivate_user(self):
        """Test user deactivation."""
        config = SecurityConfig()
        manager = UserManager(config)
        
        # Create a test user
        user = manager.create_user(
            username="testuser",
            email="test@example.com",
            password="StrongPass123!",
            role=UserRole.VIEWER
        )
        
        # Deactivate user
        success = manager.deactivate_user(user.user_id)
        
        assert success
        assert not user.is_active
    
    def test_change_password_success(self):
        """Test successful password change."""
        config = SecurityConfig()
        manager = UserManager(config)
        
        # Create a test user
        user = manager.create_user(
            username="testuser",
            email="test@example.com",
            password="OldPass123!",
            role=UserRole.VIEWER
        )
        
        # Change password
        success = manager.change_password(
            user.user_id,
            "OldPass123!",
            "NewPass123!"
        )
        
        assert success
        assert manager.password_manager.verify_password("NewPass123!", user.password_hash)
    
    def test_change_password_wrong_old_password(self):
        """Test password change with wrong old password."""
        config = SecurityConfig()
        manager = UserManager(config)
        
        # Create a test user
        user = manager.create_user(
            username="testuser",
            email="test@example.com",
            password="OldPass123!",
            role=UserRole.VIEWER
        )
        
        # Try to change password with wrong old password
        with pytest.raises(ValueError) as exc_info:
            manager.change_password(
                user.user_id,
                "WrongOldPass!",
                "NewPass123!"
            )
        
        assert "incorrect" in str(exc_info.value)


class TestAuthenticationService:
    """Test authentication service integration."""
    
    @pytest.mark.asyncio
    async def test_login_success(self):
        """Test successful login."""
        service = AuthenticationService()
        
        login_request = LoginRequest(
            username="admin",
            password="admin123!"
        )
        
        response = await service.login(login_request)
        
        assert response.access_token
        assert response.token_type == "bearer"
        assert response.user
        assert response.user["username"] == "admin"
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        service = AuthenticationService()
        
        login_request = LoginRequest(
            username="admin",
            password="wrongpassword"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await service.login(login_request)
        
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_current_user(self):
        """Test getting current user from token."""
        service = AuthenticationService()
        
        # Login to get token
        login_request = LoginRequest(
            username="admin",
            password="admin123!"
        )
        
        response = await service.login(login_request)
        
        # Create mock credentials
        from fastapi.security import HTTPAuthorizationCredentials
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=response.access_token
        )
        
        # Get current user
        token_data = await service.get_current_user(credentials)
        
        assert token_data.username == "admin"
        assert token_data.role == "admin"
        assert "user_management" in token_data.permissions


if __name__ == "__main__":
    pytest.main([__file__])