from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timezone

from .models import Book, BookCreate, BookUpdate


def calculate_total_copies(db: Session, book_id: int) -> int:
    """Calculate total copies of a book by counting all book entries with same ISBN"""
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book or not book.isbn:
            return 1
        
        # Count all books with the same ISBN
        count = db.query(func.count(Book.id)).filter(Book.isbn == book.isbn).scalar()
        return count or 1
    except SQLAlchemyError:
        return 1


def calculate_available_copies(db: Session, book_id: int) -> int:
    """Calculate available copies by counting books not currently borrowed"""
    try:
        from ..transactions.models import Transaction
        
        # Get the book's ISBN
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book or not book.isbn:
            return 1
        
        # Count total books with this ISBN
        total = db.query(func.count(Book.id)).filter(Book.isbn == book.isbn).scalar() or 1
        
        # Count currently borrowed books (books in transactions that are not returned)
        borrowed = db.query(func.count(Book.id)).join(
            Transaction, Book.id == Transaction.book_id
        ).filter(
            Book.isbn == book.isbn,
            Transaction.is_returned == False
        ).scalar() or 0
        
        available = total - borrowed
        return max(0, available)
    except SQLAlchemyError:
        return 1


def create_book(db: Session, book_data: BookCreate) -> Book:
    """Create a new book
    
    Books are tracked by ISBN - each book entry represents one physical copy
    Multiple copies of the same ISBN are allowed
    """
    try:
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
    from ..transactions.models import Transaction
    
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
    
    # For available_only filter: only include books that have at least one copy not borrowed
    if available_only:
        # Join with transactions to count borrowed copies
        query = query.outerjoin(
            Transaction, (Book.id == Transaction.book_id) & (Transaction.is_returned == False)
        ).group_by(Book.id).having(
            # Count of this book in active transactions < total count of this ISBN
            func.count(Transaction.id) < (
                db.query(func.count(Book.id)).filter(Book.isbn == Book.isbn).correlate(Book).as_scalar()
            )
        )
    
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
    """Check book availability status - calculated on demand"""
    total = calculate_total_copies(db, book.id)
    available = calculate_available_copies(db, book.id)
    
    return {
        "book_id": book.id,
        "title": book.title,
        "total_copies": total,
        "available_copies": available,
        "borrowed_copies": total - available,
        "is_available": available > 0
    }


def is_book_borrowed(db: Session, book: Book) -> bool:
    """Check if book has any borrowed copies - calculated on demand"""
    available = calculate_available_copies(db, book.id)
    total = calculate_total_copies(db, book.id)
    return available < total


def book_to_response(db: Session, book: Book) -> dict:
    """Convert book to response with calculated fields"""
    return {
        "id": book.id,
        "title": book.title,
        "isbn": book.isbn,
        "published_year": book.published_year,
        "author_id": book.author_id,
        "description": book.description,
        "total_copies": calculate_total_copies(db, book.id),
        "available_copies": calculate_available_copies(db, book.id),
        "author": {
            "id": book.author.id,
            "name": book.author.name,
            "nationality": book.author.nationality,
        } if book.author else None,
        "created_at": book.created_at,
        "updated_at": book.updated_at,
    }