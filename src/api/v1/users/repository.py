from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import List, Optional
from datetime import datetime, timezone

from .models import User, UserCreate, UserUpdate, UserRole
from api.security.password import hash_password, verify_password

def create_user(db: Session, user_data: UserCreate, role: UserRole = UserRole.REGULAR) -> User:
    """Create a new user"""
    try:
        # Check if username already exists
        existing_user = db.query(User).filter(User.username == user_data.username).first()
        if existing_user:
            raise ValueError("Username already exists")
        
        # Check if email already exists
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            raise ValueError("Email already exists")

        # Hash password
        hashed_password = hash_password(user_data.password)
        # Create user 
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            role=role,
            is_active=True
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user 
    except IntegrityError as e:
        db.rollback()
        if "username" in str(e):
            raise ValueError("Username already exists")
        if "email" in str(e):
            raise ValueError("Email already exists")
        raise ValueError(f"Data integrity error: {str(e)}")
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError(f"Database error while creating user: {str(e)}")


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID"""
    try:
        return db.query(User).filter(User.id == user_id).first()
    except SQLAlchemyError as e:
        raise RuntimeError(f"Database error while retrieving user: {str(e)}")


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username"""
    try:
        return db.query(User).filter(User.username == username).first()
    except SQLAlchemyError as e:
        raise RuntimeError(f"Database error while retrieving user: {str(e)}")


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    try:
        return db.query(User).filter(User.email == email).first()
    except SQLAlchemyError as e:
        raise RuntimeError(f"Database error while retrieving user: {str(e)}")


def get_users(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None
) -> List[User]:
    """Get multiple users with optional filtering"""
    try:
        query = db.query(User)
        
        if role:
            query = query.filter(User.role == role)
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        return query.offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        raise RuntimeError(f"Database error while retrieving users: {str(e)}")


def update_user(db: Session, user: User, user_update: UserUpdate = None, new_password: Optional[str] = None, new_role: Optional[UserRole] = None, is_active: Optional[bool] = None) -> User:
    """Update user information - handles profile updates, password, role, and active status"""
    try:
        # Update profile fields if provided
        if user_update:
            update_data = user_update.model_dump(exclude_unset=True)
            
            # Check if email is being updated and already exists
            if "email" in update_data and update_data["email"] != user.email:
                existing_email = db.query(User).filter(User.email == update_data["email"]).first()
                if existing_email:
                    raise ValueError("Email already exists")
            
            # Update fields
            for field, value in update_data.items():
                setattr(user, field, value)
        
        # Update password if provided
        if new_password is not None:
            user.hashed_password = hash_password(new_password)
        
        # Update role if provided by admin
        if new_role is not None:
            user.role = new_role
        
        # Update active status if provided
        if is_active is not None:
            user.is_active = is_active
        
        # Update timestamp and commit
        user.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)
        
        return user
    except IntegrityError as e:
        db.rollback()
        if "email" in str(e):
            raise ValueError("Email already exists")
        raise ValueError(f"Data integrity error: {str(e)}")
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError(f"Database error while updating user: {str(e)}")


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate user by username and password"""
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None
        
        # Verify password
        is_valid = verify_password(password, user.hashed_password)
        if not is_valid:
            return None
        
        # Check if user is active
        if not user.is_active:
            return None
        
        return user
    except Exception as e:
        raise RuntimeError(f"Error during authentication: {str(e)}")


def delete_user(db: Session, user: User) -> None:
    """Delete a user"""
    try:
        db.delete(user)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError(f"Database error while deleting user: {str(e)}")
