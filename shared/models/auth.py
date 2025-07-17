"""Authentication models for StreamFlow."""

from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, Field, validator


class UserRole(str, Enum):
    """User role enumeration."""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"
    OPERATOR = "operator"


class UserStatus(str, Enum):
    """User status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class User(BaseModel):
    """User model."""
    
    id: UUID = Field(default_factory=uuid4)
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    password_changed_at: Optional[datetime] = None
    permissions: List[str] = Field(default_factory=list)
    preferences: dict = Field(default_factory=dict)
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format."""
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Username can only contain letters, numbers, underscores, and hyphens")
        return v.lower()


class UserCreate(BaseModel):
    """User creation model."""
    
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    role: UserRole = UserRole.USER
    permissions: List[str] = Field(default_factory=list)
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    """User update model."""
    
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    permissions: Optional[List[str]] = None
    preferences: Optional[dict] = None


class PasswordChange(BaseModel):
    """Password change model."""
    
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class Token(BaseModel):
    """JWT token model."""
    
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token expiration time in seconds")
    refresh_token: Optional[str] = None
    scope: List[str] = Field(default_factory=list)


class TokenData(BaseModel):
    """Token data model for JWT payload."""
    
    user_id: UUID
    username: str
    role: UserRole
    permissions: List[str] = Field(default_factory=list)
    exp: datetime
    iat: datetime = Field(default_factory=datetime.utcnow)
    sub: str  # Subject (username)


class LoginRequest(BaseModel):
    """Login request model."""
    
    username: str
    password: str
    remember_me: bool = False


class LoginResponse(BaseModel):
    """Login response model."""
    
    user: User
    token: Token
    message: str = "Login successful"


class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""
    
    refresh_token: str


class UserSession(BaseModel):
    """User session model."""
    
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    token_jti: str  # JWT ID
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool = True