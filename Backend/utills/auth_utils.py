"""
Authentication utility functions.

Contains JWT token creation, validation, and user ID extraction functions.
"""

# Standard library imports
import os
from datetime import datetime, timedelta
from typing import Optional

# Third-party imports
import jwt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "dev_secret_key_change_in_production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_DAYS = int(os.getenv("JWT_EXPIRATION_DAYS", "180"))


def create_token(payload: dict, days: Optional[int] = None) -> str:
    """
    Create JWT token with expiration.
    
    Args:
        payload: Dictionary containing token payload (typically user_id)
        days: Token expiration in days (defaults to JWT_EXPIRATION_DAYS)
    
    Returns:
        str: Encoded JWT token
    """
    if days is None:
        days = JWT_EXPIRATION_DAYS
    
    to_encode = payload.copy()
    to_encode.update({
        "exp": datetime.utcnow() + timedelta(days=days),
        "iat": datetime.utcnow()
    })
    
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and validate JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        dict: Decoded token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_user_id_from_token(authorization: Optional[str]) -> Optional[str]:
    """
    Extract user ID from Authorization Bearer token.
    
    Args:
        authorization: Authorization header value (format: "Bearer <token>")
    
    Returns:
        str: User ID if token is valid, None otherwise
    """
    if not authorization:
        return None
    
    try:
        # Extract token from "Bearer <token>" format
        scheme, token = authorization.split(" ", 1)
        if scheme.lower() != "bearer":
            return None
        
        payload = decode_token(token)
        if payload:
            return payload.get("user_id")
        return None
    except (ValueError, AttributeError):
        return None

