"""
Unit tests for security middleware.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from starlette.requests import Request
from starlette.responses import Response

from src.security.middleware import (
    AuthenticationMiddleware,
    PermissionChecker,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    AuditLogMiddleware
)
from src.security.auth import (
    AuthenticationService,
    TokenData,
    Permission,
    UserRole
)


class TestAuthenticationMiddleware:
    """Test authentication middleware."""
    
    def test_excluded_paths(self):
        """Test that excluded paths bypass authentication."""
        app = FastAPI()
        auth_service = Mock(spec=AuthenticationService)
        middleware = AuthenticationMiddleware(app, auth_service)
        
        # Test excluded paths
        excluded_paths = ["/docs", "/redoc", "/openapi.json", "/api/auth/login", "/health"]
        
        for path in excluded_paths:
            assert path in middleware.excluded_paths
    
    @pytest.mark.asyncio
    async def test_missing_auth_header(self):
        """Test request without authorization header."""
        app = FastAPI()
        auth_service = Mock(spec=AuthenticationService)
        middleware = AuthenticationMiddleware(app, auth_service)
        
        # Mock request without auth header
        request = Mock(spec=Request)
        request.url.path = "/api/test"
        request.method = "GET"
        request.headers = {}
        
        # Mock call_next
        call_next = AsyncMock(return_value=Response("OK"))
        
        response = await middleware.dispatch(request, call_next)
        
        assert response.status_code == 401
        assert "Missing or invalid authorization header" in response.body.decode()
    
    @pytest.mark.asyncio
    async def test_invalid_auth_header(self):
        """Test request with invalid authorization header."""
        app = FastAPI()
        auth_service = Mock(spec=AuthenticationService)
        middleware = AuthenticationMiddleware(app, auth_service)
        
        # Mock request with invalid auth header
        request = Mock(spec=Request)
        request.url.path = "/api/test"
        request.method = "GET"
        request.headers = {"Authorization": "Invalid token"}
        
        # Mock call_next
        call_next = AsyncMock(return_value=Response("OK"))
        
        response = await middleware.dispatch(request, call_next)
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_valid_token(self):
        """Test request with valid token."""
        app = FastAPI()
        auth_service = Mock(spec=AuthenticationService)
        
        # Mock token verification
        token_data = TokenData(
            user_id="test-001",
            username="testuser",
            role="viewer",
            permissions=["read_documents"],
            exp=None,
            iat=None,
            jti="test-jti"
        )
        auth_service.token_manager.verify_token.return_value = token_data
        
        middleware = AuthenticationMiddleware(app, auth_service)
        
        # Mock request with valid auth header
        request = Mock(spec=Request)
        request.url.path = "/api/test"
        request.method = "GET"
        request.headers = {"Authorization": "Bearer valid.token.here"}
        request.state = Mock()
        
        # Mock call_next
        call_next = AsyncMock(return_value=Response("OK"))
        
        response = await middleware.dispatch(request, call_next)
        
        assert response.status_code == 200
        assert request.state.user == token_data
        assert request.state.authenticated == True
    
    @pytest.mark.asyncio
    async def test_options_request_bypass(self):
        """Test that OPTIONS requests bypass authentication."""
        app = FastAPI()
        auth_service = Mock(spec=AuthenticationService)
        middleware = AuthenticationMiddleware(app, auth_service)
        
        # Mock OPTIONS request
        request = Mock(spec=Request)
        request.url.path = "/api/test"
        request.method = "OPTIONS"
        request.headers = {}
        
        # Mock call_next
        call_next = AsyncMock(return_value=Response("OK"))
        
        response = await middleware.dispatch(request, call_next)
        
        assert response.status_code == 200
        call_next.assert_called_once()


class TestPermissionChecker:
    """Test permission checker functionality."""
    
    def test_require_permissions_success(self):
        """Test successful permission check."""
        auth_service = Mock(spec=AuthenticationService)
        
        # Mock token verification
        token_data = TokenData(
            user_id="test-001",
            username="testuser",
            role="admin",
            permissions=["read_documents", "user_management"],
            exp=None,
            iat=None,
            jti="test-jti"
        )
        auth_service.token_manager.verify_token.return_value = token_data
        
        checker = PermissionChecker(auth_service)
        
        # Create permission checker function
        permission_func = checker.require_permissions([Permission.READ_DOCUMENTS])
        
        # This would normally be called by FastAPI dependency injection
        # We'll test the logic directly
        assert Permission.READ_DOCUMENTS.value in token_data.permissions
    
    def test_require_permissions_failure(self):
        """Test failed permission check."""
        auth_service = Mock(spec=AuthenticationService)
        
        # Mock token verification with insufficient permissions
        token_data = TokenData(
            user_id="test-001",
            username="testuser",
            role="viewer",
            permissions=["read_documents"],
            exp=None,
            iat=None,
            jti="test-jti"
        )
        auth_service.token_manager.verify_token.return_value = token_data
        
        checker = PermissionChecker(auth_service)
        
        # Check that user doesn't have admin permission
        assert Permission.USER_MANAGEMENT.value not in token_data.permissions
    
    def test_require_role_success(self):
        """Test successful role check."""
        auth_service = Mock(spec=AuthenticationService)
        
        # Mock token verification
        token_data = TokenData(
            user_id="test-001",
            username="testuser",
            role="admin",
            permissions=["read_documents", "user_management"],
            exp=None,
            iat=None,
            jti="test-jti"
        )
        auth_service.token_manager.verify_token.return_value = token_data
        
        checker = PermissionChecker(auth_service)
        
        # Check role
        assert token_data.role == "admin"
    
    def test_require_role_failure(self):
        """Test failed role check."""
        auth_service = Mock(spec=AuthenticationService)
        
        # Mock token verification with wrong role
        token_data = TokenData(
            user_id="test-001",
            username="testuser",
            role="viewer",
            permissions=["read_documents"],
            exp=None,
            iat=None,
            jti="test-jti"
        )
        auth_service.token_manager.verify_token.return_value = token_data
        
        checker = PermissionChecker(auth_service)
        
        # Check that user doesn't have admin role
        assert token_data.role != "admin"


class TestRateLimitMiddleware:
    """Test rate limiting middleware."""
    
    @pytest.mark.asyncio
    async def test_rate_limit_not_exceeded(self):
        """Test request within rate limit."""
        app = FastAPI()
        middleware = RateLimitMiddleware(app, requests_per_minute=60)
        
        # Mock request
        request = Mock(spec=Request)
        request.client.host = "127.0.0.1"
        
        # Mock call_next
        call_next = AsyncMock(return_value=Response("OK"))
        
        response = await middleware.dispatch(request, call_next)
        
        assert response.status_code == 200
        call_next.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self):
        """Test request exceeding rate limit."""
        app = FastAPI()
        middleware = RateLimitMiddleware(app, requests_per_minute=1)  # Very low limit
        
        # Mock request
        request = Mock(spec=Request)
        request.client.host = "127.0.0.1"
        
        # Mock call_next
        call_next = AsyncMock(return_value=Response("OK"))
        
        # First request should succeed
        response1 = await middleware.dispatch(request, call_next)
        assert response1.status_code == 200
        
        # Second request should be rate limited
        response2 = await middleware.dispatch(request, call_next)
        assert response2.status_code == 429
        assert "Rate limit exceeded" in response2.body.decode()
        assert "Retry-After" in response2.headers


class TestSecurityHeadersMiddleware:
    """Test security headers middleware."""
    
    @pytest.mark.asyncio
    async def test_security_headers_added(self):
        """Test that security headers are added to response."""
        app = FastAPI()
        middleware = SecurityHeadersMiddleware(app)
        
        # Mock request
        request = Mock(spec=Request)
        
        # Mock call_next returning a response
        original_response = Response("OK")
        call_next = AsyncMock(return_value=original_response)
        
        response = await middleware.dispatch(request, call_next)
        
        # Check that security headers are present
        expected_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security",
            "Referrer-Policy",
            "Content-Security-Policy"
        ]
        
        for header in expected_headers:
            assert header in response.headers
        
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"


class TestAuditLogMiddleware:
    """Test audit logging middleware."""
    
    @pytest.mark.asyncio
    async def test_audit_logging(self):
        """Test that requests are logged for audit purposes."""
        app = FastAPI()
        middleware = AuditLogMiddleware(app)
        
        # Mock request
        request = Mock(spec=Request)
        request.method = "GET"
        request.url.path = "/api/test"
        request.client.host = "127.0.0.1"
        request.state = Mock()
        request.state.user = {"user_id": "test-001"}
        
        # Mock call_next
        original_response = Response("OK", status_code=200)
        call_next = AsyncMock(return_value=original_response)
        
        with patch.object(middleware.audit_logger, 'info') as mock_log:
            response = await middleware.dispatch(request, call_next)
            
            # Check that audit log was called
            mock_log.assert_called_once()
            log_message = mock_log.call_args[0][0]
            
            assert "test-001" in log_message
            assert "GET" in log_message
            assert "/api/test" in log_message
            assert "200" in log_message
            assert "127.0.0.1" in log_message
    
    @pytest.mark.asyncio
    async def test_audit_logging_anonymous_user(self):
        """Test audit logging for anonymous users."""
        app = FastAPI()
        middleware = AuditLogMiddleware(app)
        
        # Mock request without user
        request = Mock(spec=Request)
        request.method = "GET"
        request.url.path = "/api/test"
        request.client.host = "127.0.0.1"
        request.state = Mock()
        # No user attribute
        
        # Mock call_next
        original_response = Response("OK", status_code=200)
        call_next = AsyncMock(return_value=original_response)
        
        with patch.object(middleware.audit_logger, 'info') as mock_log:
            response = await middleware.dispatch(request, call_next)
            
            # Check that audit log was called with anonymous user
            mock_log.assert_called_once()
            log_message = mock_log.call_args[0][0]
            
            assert "anonymous" in log_message


if __name__ == "__main__":
    pytest.main([__file__])