from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from .models import Book, BookCreate, BookUpdate


def create_book(db: Session, book_data: BookCreate) -> Book:
    """Create a new book"""
    db_book = Book(**book_data.model_dump())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book


def get_book(db: Session, book_id: int) -> Optional[Book]:
    """Get book by ID"""
    # TODO: prefetch related author data
    return db.query(Book).filter(Book.id == book_id).first()


def get_book_by_isbn(db: Session, isbn: str) -> Optional[Book]:
    """Get book by ISBN"""
    return db.query(Book).filter(Book.isbn == isbn).first()


def get_books(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None,
    author_id: Optional[int] = None,
    available_only: bool = False
) -> List[Book]:
    """Get multiple books with filtering"""
    query = db.query(Book)
    
    # Apply filters
    if search:
        query = query.filter(
            (Book.title.ilike(f"%{search}%")) |
            (Book.isbn.ilike(f"%{search}%"))
        )
    
    if author_id:
        query = query.filter(Book.author_id == author_id)
    
    if available_only:
        query = query.filter(Book.available_copies > 0)
    
    return query.offset(skip).limit(limit).all()


def update_book(db: Session, book: Book, book_update: BookUpdate) -> Book:
    """Update book information"""
    update_data = book_update.model_dump(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc)
        for field, value in update_data.items():
            setattr(book, field, value)
        db.commit()
        db.refresh(book)
    return book


def delete_book(db: Session, book: Book) -> None:
    """Delete a book"""
    db.delete(book)
    db.commit()


def check_book_availability(db: Session, book: Book) -> dict:
    """Check book availability status"""
    return {
        "book_id": book.id,
        "title": book.title,
        "total_copies": book.total_copies,
        "available_copies": book.available_copies,
        "borrowed_copies": book.total_copies - book.available_copies,
        "is_available": book.available_copies > 0
    }


def is_book_borrowed(book: Book) -> bool:
    """Check if book has any borrowed copies"""
    return book.available_copies < book.total_copies