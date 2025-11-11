from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import List, Optional
from datetime import datetime, timezone

from .models import Book, BookCreate, BookUpdate


def create_book(db: Session, book_data: BookCreate) -> Book:
    """Create a new book
    
    If a book with the same ISBN already exists, increment total_copies
    Otherwise create a new book entry
    """
    try:
        # Check if book with same ISBN exists
        if book_data.isbn:
            existing_book = get_book_by_isbn(db, book_data.isbn)
            if existing_book:
                # Increment total_copies and available_copies
                existing_book.total_copies += 1
                existing_book.available_copies += 1
                existing_book.updated_at = datetime.now(timezone.utc)
                db.commit()
                db.refresh(existing_book)
                return existing_book
        
        # Create new book entry
        db_book = Book(**book_data.model_dump())
        db.add(db_book)
        db.commit()
        db.refresh(db_book)
        return db_book
    except IntegrityError as e:
        db.rollback()
        # Foreign key constraint violation (author doesn't exist)
        if "author_id" in str(e):
            raise ValueError("Author with the specified ID does not exist")
        # Unique constraint violation (ISBN already exists)
        if "isbn" in str(e):
            raise ValueError("Book with this ISBN already exists")
        raise ValueError(f"Data integrity error: {str(e)}")
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError(f"Database error while creating book: {str(e)}")


def get_book(db: Session, book_id: int) -> Optional[Book]:
    """Get book by ID with author data"""
    return db.query(Book).options(
        selectinload(Book.author)
    ).filter(Book.id == book_id).first()


def get_book_by_isbn(db: Session, isbn: str) -> Optional[Book]:
    """Get book by ISBN with author data"""
    return db.query(Book).options(
        selectinload(Book.author)
    ).filter(Book.isbn == isbn).first()


def get_books(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None,
    author_id: Optional[int] = None,
    available_only: bool = False
) -> List[Book]:
    """Get multiple books with filtering and prefetched author data"""
    from ..authors.models import Author
    
    query = db.query(Book).options(
        selectinload(Book.author)
    )
    
    # Apply filters
    if search:
        # Join with author for name search, use LEFT JOIN to include books without authors
        query = query.outerjoin(Author, Book.author_id == Author.id).filter(
            (Book.title.ilike(f"%{search}%")) |
            (Book.isbn.ilike(f"%{search}%")) |
            (Author.name.ilike(f"%{search}%"))
        )
    
    if author_id:
        query = query.filter(Book.author_id == author_id)
    
    if available_only:
        query = query.filter(Book.available_copies > 0)
    
    return query.offset(skip).limit(limit).all()


def update_book(db: Session, book: Book, book_update: BookUpdate) -> Book:
    """Update book information and return with author data"""
    try:
        update_data = book_update.model_dump(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.now(timezone.utc)
            for field, value in update_data.items():
                setattr(book, field, value)
            db.commit()
            db.refresh(book)
            
            # If author_id was updated, reload the book with new author data
            if 'author_id' in update_data:
                return get_book(db, book.id)
        
        return book
    except IntegrityError as e:
        db.rollback()
        if "author_id" in str(e):
            raise ValueError("Author with the specified ID does not exist")
        if "isbn" in str(e):
            raise ValueError("Book with this ISBN already exists")
        raise ValueError(f"Data integrity error: {str(e)}")
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError(f"Database error while updating book: {str(e)}")


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