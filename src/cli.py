"""
CLI script to create admin users
Usage: python cli.py

Or set environment variables:
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=password123
ADMIN_FULLNAME=Admin User (optional)
"""

import sys
import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from api.db.config import DATABASE_URL
from api.v1.users.models import UserRole
from api.v1.users.repository import create_user, get_user_by_username
from api.v1.users.models import UserCreate


# Create engine and session
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables"""
    from api.v1.authors.models import Author
    from api.v1.books.models import Book
    
    SQLModel.metadata.create_all(engine)


def create_admin():
    """Create a new admin user"""
    try:
        # Initialize database
        init_db()
        
        db = SessionLocal()
        
        # Get input from environment variables or prompt user
        username = os.getenv('ADMIN_USERNAME') or input('Username: ')
        email = os.getenv('ADMIN_EMAIL') or input('Email: ')
        password = os.getenv('ADMIN_PASSWORD') or input('Password: ')
        full_name = os.getenv('ADMIN_FULLNAME', '')
        
        # Check if user already exists
        existing_user = get_user_by_username(db, username)
        if existing_user:
            print(f"❌ User '{username}' already exists!")
            return
        
        # Create user data
        user_data = UserCreate(
            username=username,
            email=email,
            password=password,
            full_name=full_name or None
        )
        
        # Create admin user
        admin_user = create_user(db, user_data, role=UserRole.ADMIN)
        
        print(f"✅ Admin user created successfully!")
        print(f"   Username: {admin_user.username}")
        print(f"   Email: {admin_user.email}")
        print(f"   Role: {admin_user.role.value}")
        print(f"   ID: {admin_user.id}")
        
    except ValueError as e:
        print(f"❌ Error: {str(e)}")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
    finally:
        db.close()


if __name__ == '__main__':
    create_admin()