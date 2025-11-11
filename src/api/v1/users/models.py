from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Index
from enum import Enum


class UserRole(str, Enum):
    """User role enumeration"""
    ADMIN = "admin"
    REGULAR = "regular"


class UserBase(SQLModel):
    """Base User model with shared fields"""
    username: str = Field(min_length=3, max_length=50, unique=True)
    email: str = Field(max_length=254, unique=True)
    full_name: Optional[str] = Field(default=None, max_length=200)
    is_active: bool = Field(default=True)
    role: UserRole = Field(default=UserRole.REGULAR)


class User(UserBase, table=True):
    """User database model"""
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str = Field(min_length=60)  # For bcrypt hashes
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Add indexes for better query performance
    __table_args__ = (
        Index('idx_user_username', 'username'),
        Index('idx_user_email', 'email'),
        Index('idx_user_is_active', 'is_active'),
        Index('idx_user_role', 'role'),
    )


class UserCreate(SQLModel):
    """Schema for creating a new user"""
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(max_length=254)
    password: str = Field(min_length=8, max_length=100)
    full_name: Optional[str] = Field(default=None, max_length=200)


class UserUpdate(SQLModel):
    """Schema for updating a user"""
    email: Optional[str] = Field(default=None, max_length=254)
    full_name: Optional[str] = Field(default=None, max_length=200)
    is_active: Optional[bool] = Field(default=None)


class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    created_at: datetime
    updated_at: datetime


class UserLogin(SQLModel):
    """Schema for user login"""
    username: str
    password: str


class TokenResponse(SQLModel):
    """Schema for token response"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
