import os
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from decouple import config as decouple_config

# JWT configuration
SECRET_KEY = decouple_config("SECRET_KEY", default="your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(decouple_config("ACCESS_TOKEN_EXPIRE_MINUTES", default="30"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time delta
    
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    # Ensure 'sub' claim is a string (PyJWT requirement)
    if "sub" in to_encode and not isinstance(to_encode["sub"], str):
        to_encode["sub"] = str(to_encode["sub"])
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def verify_token(token: str) -> dict:
    """
    Verify and decode JWT token
    
    Args:
        token: JWT token to verify
    
    Returns:
        Decoded token payload
    
    Raises:
        jwt.InvalidTokenError: If token is invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Convert 'sub' back to integer if present
        if "sub" in payload and isinstance(payload["sub"], str):
            payload["sub"] = int(payload["sub"])
        return payload
    except jwt.ExpiredSignatureError as e:
        raise jwt.InvalidTokenError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise jwt.InvalidTokenError("Invalid token")
