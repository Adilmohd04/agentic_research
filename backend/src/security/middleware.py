"""
Security Middleware for Authentication and Authorization

This module provides middleware for request authentication, authorization,
and permission checking.
"""

import logging
from typing import Optional, List, Callable
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from .auth import AuthenticationService, TokenData, Permission

logger = logging.getLogger(__name__)

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for request authentication."""
    
    def __init__(self, app, auth_service: AuthenticationService):
        super().__init__(app)
        self.auth_service = auth_service
        self.excluded_paths = {
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/auth/login",
            "/api/auth/register",
            "/health",
            "/metrics"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request authentication."""
        # Skip authentication for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)
        
        # Skip authentication for OPTIONS requests
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return Response(
                content="Missing or invalid authorization header",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        
        token = auth_header.split(" ")[1]
        
        try:
            # Verify token and get user data
            token_data = self.auth_service.token_manager.verify_token(token)
            
            # Add user data to request state
            request.state.user = token_data
            request.state.authenticated = True
            
            # Log successful authentication
            logger.debug(f"Authenticated user: {token_data.username}")
            
        except HTTPException as e:
            return Response(
                content=e.detail,
                status_code=e.status_code
            )
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return Response(
                content="Authentication failed",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        
        return await call_next(request)

class PermissionChecker:
    """Permission checking utilities."""
    
    def __init__(self, auth_service: AuthenticationService):
        self.auth_service = auth_service
        self.security = HTTPBearer()
    
    def require_permissions(self, required_permissions: List[Permission]):
        """Dependency for requiring specific permissions."""
        async def check_permissions(
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ) -> TokenData:
            # Verify token
            token_data = self.auth_service.token_manager.verify_token(credentials.credentials)
            
            # Check permissions
            user_permissions = set(token_data.permissions)
            required_permission_values = {p.value for p in required_permissions}
            
            if not required_permission_values.issubset(user_permissions):
                missing_permissions = required_permission_values - user_permissions
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permissions: {', '.join(missing_permissions)}"
                )
            
            return token_data
        
        return check_permissions
    
    def require_role(self, required_roles: List[str]):
        """Dependency for requiring specific roles."""
        async def check_role(
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ) -> TokenData:
            # Verify token
            token_data = self.auth_service.token_manager.verify_token(credentials.credentials)
            
            # Check role
            if token_data.role not in required_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Required role not found. User role: {token_data.role}, Required: {required_roles}"
                )
            
            return token_data
        
        return check_role
    
    def get_current_user(self):
        """Dependency for getting current authenticated user."""
        async def _get_current_user(
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ) -> TokenData:
            return self.auth_service.token_manager.verify_token(credentials.credentials)
        
        return _get_current_user

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts = {}  # In production, use Redis
        self.window_size = 60  # 1 minute window
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting."""
        # Get client IP
        client_ip = request.client.host
        
        # Get current time window
        import time
        current_window = int(time.time()) // self.window_size
        
        # Initialize or update request count
        key = f"{client_ip}:{current_window}"
        
        if key not in self.request_counts:
            self.request_counts[key] = 0
        
        self.request_counts[key] += 1
        
        # Check rate limit
        if self.request_counts[key] > self.requests_per_minute:
            return Response(
                content="Rate limit exceeded",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={"Retry-After": str(self.window_size)}
            )
        
        # Clean up old entries
        self._cleanup_old_entries(current_window)
        
        return await call_next(request)
    
    def _cleanup_old_entries(self, current_window: int):
        """Clean up old rate limit entries."""
        keys_to_remove = []
        for key in self.request_counts:
            window = int(key.split(":")[1])
            if window < current_window - 1:  # Keep current and previous window
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.request_counts[key]

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response

class AuditLogMiddleware(BaseHTTPMiddleware):
    """Middleware for audit logging."""
    
    def __init__(self, app):
        super().__init__(app)
        self.audit_logger = logging.getLogger("audit")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request for audit purposes."""
        import time
        start_time = time.time()
        
        # Get user info if available
        user_id = getattr(request.state, 'user', {}).get('user_id', 'anonymous')
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log audit information
        self.audit_logger.info(
            f"User: {user_id} | "
            f"Method: {request.method} | "
            f"Path: {request.url.path} | "
            f"Status: {response.status_code} | "
            f"Time: {process_time:.3f}s | "
            f"IP: {request.client.host}"
        )
        
        return response