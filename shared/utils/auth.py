"""Authentication utilities for StreamFlow."""

import secrets
from datetime import datetime, timedelta
from typing import Optional, Union

import bcrypt
from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import get_settings
from ..models.auth import TokenData, User

settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.jwt_secret_key, 
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.jwt_refresh_expire_days)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt


def decode_token(token: str) -> Optional[TokenData]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
            
        token_data = TokenData(
            user_id=payload.get("user_id"),
            username=payload.get("username"),
            role=payload.get("role"),
            permissions=payload.get("permissions", []),
            exp=datetime.fromtimestamp(payload.get("exp")),
            iat=datetime.fromtimestamp(payload.get("iat")),
            sub=user_id
        )
        
        return token_data
        
    except JWTError:
        return None


def generate_api_key() -> str:
    """Generate a secure API key."""
    return secrets.token_urlsafe(32)


def validate_token_expiry(token_data: TokenData) -> bool:
    """Check if token has expired."""
    return datetime.utcnow() < token_data.exp


def create_password_reset_token(user_id: str) -> str:
    """Create a password reset token."""
    data = {
        "sub": str(user_id),
        "type": "password_reset",
        "exp": datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry
    }
    
    return jwt.encode(
        data,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )


def verify_password_reset_token(token: str) -> Optional[str]:
    """Verify password reset token and return user ID."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        if payload.get("type") != "password_reset":
            return None
            
        user_id: str = payload.get("sub")
        return user_id
        
    except JWTError:
        return None


def check_permission(user: User, required_permission: str) -> bool:
    """Check if user has required permission."""
    if user.role == "admin":
        return True
    
    return required_permission in user.permissions


def get_permissions_for_role(role: str) -> list[str]:
    """Get default permissions for a role."""
    role_permissions = {
        "admin": [
            "users:read", "users:write", "users:delete",
            "alerts:read", "alerts:write", "alerts:delete",
            "metrics:read", "metrics:write",
            "events:read", "events:write",
            "dashboards:read", "dashboards:write", "dashboards:delete",
            "settings:read", "settings:write"
        ],
        "operator": [
            "alerts:read", "alerts:write",
            "metrics:read",
            "events:read",
            "dashboards:read", "dashboards:write"
        ],
        "user": [
            "alerts:read",
            "metrics:read",
            "events:read",
            "dashboards:read"
        ],
        "viewer": [
            "metrics:read",
            "events:read",
            "dashboards:read"
        ]
    }
    
    return role_permissions.get(role, [])