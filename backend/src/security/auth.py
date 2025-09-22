"""
Authentication and Authorization System

This module provides comprehensive authentication and authorization capabilities
including JWT tokens, role-based access control (RBAC), and permission checking.
"""

import jwt
import bcrypt
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict
from enum import Enum
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import secrets

logger = logging.getLogger(__name__)

class UserRole(Enum):
    """User roles for RBAC."""
    ADMIN = "admin"
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    VIEWER = "viewer"
    GUEST = "guest"

class Permission(Enum):
    """System permissions."""
    # Document permissions
    READ_DOCUMENTS = "read_documents"
    WRITE_DOCUMENTS = "write_documents"
    DELETE_DOCUMENTS = "delete_documents"
    SHARE_DOCUMENTS = "share_documents"
    
    # Agent permissions
    USE_AGENTS = "use_agents"
    CONFIGURE_AGENTS = "configure_agents"
    VIEW_AGENT_LOGS = "view_agent_logs"
    
    # System permissions
    ADMIN_PANEL = "admin_panel"
    USER_MANAGEMENT = "user_management"
    SYSTEM_CONFIG = "system_config"
    VIEW_ANALYTICS = "view_analytics"
    
    # Voice interface permissions
    USE_VOICE = "use_voice"
    CONFIGURE_VOICE = "configure_voice"
    
    # Developer copilot permissions
    USE_COPILOT = "use_copilot"
    REPOSITORY_ACCESS = "repository_access"

@dataclass
class User:
    """User model."""
    user_id: str
    username: str
    email: str
    password_hash: str
    role: UserRole
    permissions: Set[Permission]
    is_active: bool = True
    created_at: datetime = None
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

@dataclass
class TokenData:
    """JWT token data."""
    user_id: str
    username: str
    role: str
    permissions: List[str]
    exp: datetime
    iat: datetime
    jti: str  # JWT ID for token revocation

@dataclass
class LoginRequest:
    """Login request data."""
    username: str
    password: str
    remember_me: bool = False

@dataclass
class LoginResponse:
    """Login response data."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    user: Dict[str, Any] = None

class SecurityConfig:
    """Security configuration."""
    
    def __init__(self):
        self.jwt_secret_key = self._generate_secret_key()
        self.jwt_algorithm = "HS256"
        self.access_token_expire_minutes = 60
        self.refresh_token_expire_days = 30
        self.max_failed_login_attempts = 5
        self.account_lockout_duration_minutes = 30
        self.password_min_length = 8
        self.require_password_complexity = True
        self.session_timeout_minutes = 120
    
    def _generate_secret_key(self) -> str:
        """Generate a secure secret key."""
        return secrets.token_urlsafe(32)

class PasswordManager:
    """Password hashing and validation."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    @staticmethod
    def validate_password_strength(password: str, config: SecurityConfig) -> List[str]:
        """Validate password strength and return list of issues."""
        issues = []
        
        if len(password) < config.password_min_length:
            issues.append(f"Password must be at least {config.password_min_length} characters long")
        
        if config.require_password_complexity:
            if not any(c.isupper() for c in password):
                issues.append("Password must contain at least one uppercase letter")
            
            if not any(c.islower() for c in password):
                issues.append("Password must contain at least one lowercase letter")
            
            if not any(c.isdigit() for c in password):
                issues.append("Password must contain at least one digit")
            
            if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
                issues.append("Password must contain at least one special character")
        
        return issues


class RolePermissionManager:
    """Manages role-based permissions."""
    
    def __init__(self):
        self.role_permissions = self._initialize_role_permissions()
    
    def _initialize_role_permissions(self) -> Dict[UserRole, Set[Permission]]:
        """Initialize default role permissions."""
        return {
            UserRole.ADMIN: {
                # All permissions
                Permission.READ_DOCUMENTS,
                Permission.WRITE_DOCUMENTS,
                Permission.DELETE_DOCUMENTS,
                Permission.SHARE_DOCUMENTS,
                Permission.USE_AGENTS,
                Permission.CONFIGURE_AGENTS,
                Permission.VIEW_AGENT_LOGS,
                Permission.ADMIN_PANEL,
                Permission.USER_MANAGEMENT,
                Permission.SYSTEM_CONFIG,
                Permission.VIEW_ANALYTICS,
                Permission.USE_VOICE,
                Permission.CONFIGURE_VOICE,
                Permission.USE_COPILOT,
                Permission.REPOSITORY_ACCESS
            },
            UserRole.RESEARCHER: {
                Permission.READ_DOCUMENTS,
                Permission.WRITE_DOCUMENTS,
                Permission.SHARE_DOCUMENTS,
                Permission.USE_AGENTS,
                Permission.VIEW_AGENT_LOGS,
                Permission.VIEW_ANALYTICS,
                Permission.USE_VOICE,
                Permission.USE_COPILOT,
                Permission.REPOSITORY_ACCESS
            },
            UserRole.ANALYST: {
                Permission.READ_DOCUMENTS,
                Permission.WRITE_DOCUMENTS,
                Permission.USE_AGENTS,
                Permission.VIEW_AGENT_LOGS,
                Permission.VIEW_ANALYTICS,
                Permission.USE_VOICE
            },
            UserRole.VIEWER: {
                Permission.READ_DOCUMENTS,
                Permission.USE_AGENTS,
                Permission.USE_VOICE
            },
            UserRole.GUEST: {
                Permission.READ_DOCUMENTS
            }
        }
    
    def get_role_permissions(self, role: UserRole) -> Set[Permission]:
        """Get permissions for a role."""
        return self.role_permissions.get(role, set())
    
    def has_permission(self, user_role: UserRole, permission: Permission) -> bool:
        """Check if a role has a specific permission."""
        return permission in self.get_role_permissions(user_role)

class TokenManager:
    """JWT token management."""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.revoked_tokens: Set[str] = set()  # In production, use Redis or database
    
    def create_access_token(self, user: User) -> str:
        """Create JWT access token."""
        now = datetime.utcnow()
        exp = now + timedelta(minutes=self.config.access_token_expire_minutes)
        jti = secrets.token_urlsafe(16)
        
        payload = {
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role.value,
            "permissions": [p.value for p in user.permissions],
            "exp": exp,
            "iat": now,
            "jti": jti,
            "type": "access"
        }
        
        return jwt.encode(payload, self.config.jwt_secret_key, algorithm=self.config.jwt_algorithm)
    
    def verify_token(self, token: str) -> TokenData:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(
                token, 
                self.config.jwt_secret_key, 
                algorithms=[self.config.jwt_algorithm]
            )
            
            # Check if token is revoked
            jti = payload.get("jti")
            if jti in self.revoked_tokens:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
                )
            
            return TokenData(
                user_id=payload["user_id"],
                username=payload["username"],
                role=payload["role"],
                permissions=payload["permissions"],
                exp=datetime.fromtimestamp(payload["exp"]),
                iat=datetime.fromtimestamp(payload["iat"]),
                jti=payload["jti"]
            )
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )


class UserManager:
    """User management operations."""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.password_manager = PasswordManager()
        self.role_manager = RolePermissionManager()
        self.users: Dict[str, User] = {}  # In production, use database
        self.users_by_email: Dict[str, str] = {}  # email -> user_id mapping
        
        # Create default admin user
        self._create_default_admin()
    
    def _create_default_admin(self):
        """Create default admin user."""
        admin_id = "admin-001"
        admin_user = User(
            user_id=admin_id,
            username="admin",
            email="admin@example.com",
            password_hash=self.password_manager.hash_password("admin123!"),
            role=UserRole.ADMIN,
            permissions=self.role_manager.get_role_permissions(UserRole.ADMIN)
        )
        
        self.users[admin_id] = admin_user
        self.users_by_email[admin_user.email] = admin_id
        logger.info("Default admin user created")
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username/password."""
        # Find user by username or email
        user = None
        for u in self.users.values():
            if u.username == username or u.email == username:
                user = u
                break
        
        if not user:
            return None
        
        # Check if account is locked
        if user.locked_until and datetime.utcnow() < user.locked_until:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Account locked until {user.locked_until}"
            )
        
        # Check if account is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled"
            )
        
        # Verify password
        if self.password_manager.verify_password(password, user.password_hash):
            # Reset failed login attempts on successful login
            user.failed_login_attempts = 0
            user.locked_until = None
            user.last_login = datetime.utcnow()
            return user
        else:
            # Increment failed login attempts
            user.failed_login_attempts += 1
            
            # Lock account if too many failed attempts
            if user.failed_login_attempts >= self.config.max_failed_login_attempts:
                user.locked_until = datetime.utcnow() + timedelta(
                    minutes=self.config.account_lockout_duration_minutes
                )
                logger.warning(f"Account locked for user: {username}")
            
            return None
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self.users.get(user_id)
    
    def list_users(self) -> List[User]:
        """List all users."""
        return list(self.users.values())
    
    def create_user(self, username: str, email: str, password: str, role: UserRole) -> User:
        """Create a new user."""
        # Check if username already exists
        for user in self.users.values():
            if user.username == username:
                raise ValueError(f"Username '{username}' already exists")
            if user.email == email:
                raise ValueError(f"Email '{email}' already exists")
        
        # Validate password strength
        password_issues = self.password_manager.validate_password_strength(password, self.config)
        if password_issues:
            raise ValueError(f"Password validation failed: {'; '.join(password_issues)}")
        
        # Create new user
        user_id = f"user-{len(self.users) + 1:03d}"
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            password_hash=self.password_manager.hash_password(password),
            role=role,
            permissions=self.role_manager.get_role_permissions(role)
        )
        
        # Store user
        self.users[user_id] = user
        self.users_by_email[email] = user_id
        
        logger.info(f"User created: {username} with role {role.value}")
        return user
    
    def update_user_role(self, user_id: str, new_role: UserRole) -> bool:
        """Update user role and permissions."""
        user = self.users.get(user_id)
        if not user:
            return False
        
        old_role = user.role
        user.role = new_role
        user.permissions = self.role_manager.get_role_permissions(new_role)
        
        logger.info(f"User role updated: {user.username} from {old_role.value} to {new_role.value}")
        return True
    
    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate user account."""
        user = self.users.get(user_id)
        if not user:
            return False
        
        user.is_active = False
        logger.info(f"User deactivated: {user.username}")
        return True
    
    def activate_user(self, user_id: str) -> bool:
        """Activate user account."""
        user = self.users.get(user_id)
        if not user:
            return False
        
        user.is_active = True
        user.failed_login_attempts = 0
        user.locked_until = None
        logger.info(f"User activated: {user.username}")
        return True
    
    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """Change user password."""
        user = self.users.get(user_id)
        if not user:
            return False
        
        # Verify old password
        if not self.password_manager.verify_password(old_password, user.password_hash):
            raise ValueError("Current password is incorrect")
        
        # Validate new password strength
        password_issues = self.password_manager.validate_password_strength(new_password, self.config)
        if password_issues:
            raise ValueError(f"Password validation failed: {'; '.join(password_issues)}")
        
        # Update password
        user.password_hash = self.password_manager.hash_password(new_password)
        logger.info(f"Password changed for user: {user.username}")
        return True

class AuthenticationService:
    """Main authentication service."""
    
    def __init__(self):
        self.config = SecurityConfig()
        self.user_manager = UserManager(self.config)
        self.token_manager = TokenManager(self.config)
        self.security_bearer = HTTPBearer()
    
    async def login(self, login_request: LoginRequest) -> LoginResponse:
        """Authenticate user and return tokens."""
        user = self.user_manager.authenticate_user(
            login_request.username, 
            login_request.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Create tokens
        access_token = self.token_manager.create_access_token(user)
        
        # Prepare user data for response (exclude sensitive info)
        user_data = {
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "permissions": [p.value for p in user.permissions],
            "last_login": user.last_login.isoformat() if user.last_login else None
        }
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=access_token,  # Simplified for now
            expires_in=self.config.access_token_expire_minutes * 60,
            user=user_data
        )
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials) -> TokenData:
        """Get current user from token."""
        token = credentials.credentials
        return self.token_manager.verify_token(token)