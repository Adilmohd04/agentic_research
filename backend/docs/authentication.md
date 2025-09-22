# Authentication and Authorization System

## Overview

The Agentic Research Copilot implements a comprehensive authentication and authorization system with JWT tokens, role-based access control (RBAC), and security middleware.

## Features

### Authentication
- **JWT Token-based Authentication**: Secure token-based authentication using JSON Web Tokens
- **Password Security**: Bcrypt hashing with configurable complexity requirements
- **Account Security**: Failed login attempt tracking and account lockout protection
- **Session Management**: Configurable token expiration and refresh capabilities

### Authorization
- **Role-Based Access Control (RBAC)**: Five predefined user roles with different permission levels
- **Granular Permissions**: Fine-grained permission system for different system features
- **Permission Checking**: Middleware and dependency injection for endpoint protection

### Security Features
- **Rate Limiting**: Configurable request rate limiting per IP address
- **Security Headers**: Automatic security headers (HSTS, CSP, XSS protection, etc.)
- **Audit Logging**: Comprehensive logging of all authentication and authorization events
- **Data Encryption**: Secure password hashing and token signing

## User Roles

### Admin
- **Full system access**
- **Permissions**: All permissions including user management and system configuration
- **Use cases**: System administrators, IT staff

### Researcher
- **Research and analysis features**
- **Permissions**: Document access, agent usage, voice interface, developer copilot
- **Use cases**: Research professionals, data analysts

### Analyst
- **Data analysis capabilities**
- **Permissions**: Document access, agent usage, analytics viewing
- **Use cases**: Business analysts, data scientists

### Viewer
- **Read-only access**
- **Permissions**: Document reading, basic agent usage
- **Use cases**: Stakeholders, reviewers

### Guest
- **Limited public access**
- **Permissions**: Read-only document access
- **Use cases**: External users, temporary access

## API Endpoints

### Authentication Endpoints

#### POST /api/auth/login
Login with username/email and password.

**Request:**
```json
{
  "username": "admin",
  "password": "admin123!",
  "remember_me": false
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "user_id": "admin-001",
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin",
    "permissions": ["read_documents", "write_documents", ...],
    "last_login": "2024-01-01T12:00:00Z"
  }
}
```

#### POST /api/auth/logout
Logout current user (revokes token).

**Headers:** `Authorization: Bearer <token>`

#### GET /api/auth/me
Get current user information.

**Headers:** `Authorization: Bearer <token>`

#### GET /api/auth/permissions
Get current user's permissions.

**Headers:** `Authorization: Bearer <token>`

### Admin Endpoints

#### GET /api/auth/roles
Get all available user roles (admin only).

#### GET /api/auth/permissions/all
Get all available permissions (admin only).

#### GET /api/auth/users
List all users (admin only).

#### POST /api/auth/users
Create a new user (admin only).

**Request:**
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "StrongPass123!",
  "role": "viewer"
}
```

#### PUT /api/auth/users/{user_id}/role
Update user role (admin only).

#### PUT /api/auth/users/{user_id}/deactivate
Deactivate user account (admin only).

#### PUT /api/auth/password
Change current user's password.

## Usage Examples

### Basic Authentication

```python
from fastapi import Depends
from src.security.middleware import PermissionChecker
from src.security.auth import Permission

# Get permission checker
permission_checker = PermissionChecker(auth_service)

# Protect endpoint with authentication
@app.get("/protected")
async def protected_endpoint(
    current_user = Depends(permission_checker.get_current_user())
):
    return {"message": f"Hello {current_user.username}"}
```

### Permission-Based Protection

```python
# Require specific permissions
@app.get("/admin-only")
async def admin_endpoint(
    current_user = Depends(
        permission_checker.require_permissions([Permission.USER_MANAGEMENT])
    )
):
    return {"message": "Admin access granted"}
```

### Role-Based Protection

```python
# Require specific role
@app.get("/researcher-only")
async def researcher_endpoint(
    current_user = Depends(
        permission_checker.require_role(["researcher", "admin"])
    )
):
    return {"message": "Researcher access granted"}
```

## Security Configuration

### Password Requirements
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character

### Token Configuration
- Access token expiration: 60 minutes (configurable)
- Refresh token expiration: 30 days (configurable)
- JWT algorithm: HS256
- Secure secret key generation

### Rate Limiting
- Default: 100 requests per minute per IP
- Configurable per endpoint
- Exponential backoff for repeated violations

### Account Security
- Maximum failed login attempts: 5
- Account lockout duration: 30 minutes
- Automatic unlock after lockout period

## Security Best Practices

### For Developers
1. **Always use HTTPS** in production
2. **Validate all inputs** before processing
3. **Use dependency injection** for authentication checks
4. **Log security events** for audit trails
5. **Rotate JWT secrets** regularly
6. **Implement proper error handling** without information leakage

### For Administrators
1. **Use strong passwords** for all accounts
2. **Regularly review user permissions** and roles
3. **Monitor audit logs** for suspicious activity
4. **Keep the system updated** with security patches
5. **Implement network security** (firewalls, VPNs)
6. **Regular security assessments** and penetration testing

## Troubleshooting

### Common Issues

#### "Invalid token" errors
- Check token expiration
- Verify token format (Bearer prefix)
- Ensure secret key consistency

#### "Permission denied" errors
- Verify user role and permissions
- Check endpoint permission requirements
- Confirm user account is active

#### Account lockout issues
- Check failed login attempt count
- Verify lockout duration settings
- Reset lockout manually if needed

### Debugging

Enable debug logging for authentication:

```python
import logging
logging.getLogger("src.security").setLevel(logging.DEBUG)
```

Check audit logs for detailed request information:

```python
import logging
audit_logger = logging.getLogger("audit")
```

## Testing

Run authentication tests:

```bash
# Unit tests
python -m pytest backend/tests/test_auth.py -v

# Integration tests
python -m pytest backend/tests/test_auth_integration.py -v

# Security middleware tests
python -m pytest backend/tests/test_security_middleware.py -v
```

## Default Credentials

**Admin User:**
- Username: `admin`
- Password: `admin123!`
- Role: `admin`

> **Warning**: Change the default admin password immediately in production!

## Environment Variables

```bash
# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Security Configuration
MAX_FAILED_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_DURATION_MINUTES=30
PASSWORD_MIN_LENGTH=8

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=100
```