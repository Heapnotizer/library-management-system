from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import List, Optional
from datetime import datetime, timezone

from .models import Author, AuthorCreate, AuthorUpdate


def create_author(db: Session, author_data: AuthorCreate) -> Author:
    """Create a new author"""
    try:
        db_author = Author(**author_data.model_dump())
        db.add(db_author)
        db.commit()
        db.refresh(db_author)
        return db_author
    except IntegrityError as e:
        db.rollback()
        # Email unique constraint violation
        if "email" in str(e):
            raise ValueError("Author with this email already exists")
        raise ValueError(f"Data integrity error: {str(e)}")
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError(f"Database error while creating author: {str(e)}")


def get_author(db: Session, author_id: int) -> Optional[Author]:
    """Get author by ID with books data"""
    try:
        return db.query(Author).options(
            selectinload(Author.books)
        ).filter(Author.id == author_id).first()
    except SQLAlchemyError as e:
        raise RuntimeError(f"Database error while retrieving author: {str(e)}")


def get_author_by_email(db: Session, email: str) -> Optional[Author]:
    """Get author by email"""
    try:
        return db.query(Author).filter(Author.email == email).first()
    except SQLAlchemyError as e:
        raise RuntimeError(f"Database error while retrieving author: {str(e)}")


def get_authors(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None,
    nationality: Optional[str] = None
) -> List[Author]:
    """Get multiple authors with filtering and prefetched books data"""
    try:
        query = db.query(Author).options(
            selectinload(Author.books)
        )
        
        # Apply filters
        if search:
            query = query.filter(
                (Author.name.ilike(f"%{search}%")) |
                (Author.email.ilike(f"%{search}%"))
            )
        
        if nationality:
            query = query.filter(Author.nationality.ilike(f"%{nationality}%"))
        
        return query.offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        raise RuntimeError(f"Database error while retrieving authors: {str(e)}")


def update_author(db: Session, author: Author, author_update: AuthorUpdate) -> Author:
    """Update author information and return with books data"""
    try:
        update_data = author_update.model_dump(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.now(timezone.utc)
            for field, value in update_data.items():
                setattr(author, field, value)
            db.commit()
            db.refresh(author)
            
            # If email was updated, reload the author with books data
            if 'email' in update_data:
                return get_author(db, author.id)
        
        return author
    except IntegrityError as e:
        db.rollback()
        if "email" in str(e):
            raise ValueError("Author with this email already exists")
        raise ValueError(f"Data integrity error: {str(e)}")
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError(f"Database error while updating author: {str(e)}")


def delete_author(db: Session, author: Author) -> None:
    """Delete an author"""
    try:
        db.delete(author)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError(f"Database error while deleting author: {str(e)}")