from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from .models import BookCreate, BookUpdate, BookResponse
from .repository import (
    create_book, get_book, get_book_by_isbn, get_books, 
    update_book, delete_book, check_book_availability, is_book_borrowed
)
from ...db.session import get_session

router = APIRouter()

@router.post("/", response_model=BookResponse, status_code=201)
async def create_book_endpoint(
    book_data: BookCreate,
    db: Session = Depends(get_session)
):
    """Create a new book in the library"""
    try:
        # Check if book with same ISBN already exists
        if book_data.isbn:
            existing_book = get_book_by_isbn(db, book_data.isbn)
            if existing_book:
                raise HTTPException(
                    status_code=400,
                    detail=f"Book with ISBN {book_data.isbn} already exists"
                )
        
        # Create new book using CRUD function
        return create_book(db, book_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred while creating the book")

@router.get("/", response_model=List[BookResponse])
async def get_books_endpoint(
    skip: int = Query(0, ge=0, description="Number of books to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of books to return"),
    search: Optional[str] = Query(None, description="Search by title or ISBN"),
    author_id: Optional[int] = Query(None, description="Filter by author ID"),
    available_only: bool = Query(False, description="Show only available books"),
    db: Session = Depends(get_session)
):
    """Get list of books with optional filtering and pagination"""
    return get_books(
        db=db,
        skip=skip,
        limit=limit,
        search=search,
        author_id=author_id,
        available_only=available_only
    )

@router.get("/{book_id}", response_model=BookResponse)
async def get_book_endpoint(
    book_id: int,
    db: Session = Depends(get_session)
):
    """Get details of a specific book"""
    book = get_book(db, book_id)
    if not book:
        raise HTTPException(
            status_code=404,
            detail=f"Book with ID {book_id} not found"
        )
    return book

@router.patch("/{book_id}", response_model=BookResponse)
async def update_book_endpoint(
    book_id: int,
    book_update: BookUpdate,
    db: Session = Depends(get_session)
):
    """Update book information"""
    try:
        book = get_book(db, book_id)
        if not book:
            raise HTTPException(
                status_code=404,
                detail=f"Book with ID {book_id} not found"
            )
        
        # Check if ISBN is being updated and already exists
        if book_update.isbn and book_update.isbn != book.isbn:
            existing_book = get_book_by_isbn(db, book_update.isbn)
            if existing_book:
                raise HTTPException(
                    status_code=400,
                    detail=f"Book with ISBN {book_update.isbn} already exists"
                )
        
        # Update using CRUD function
        return update_book(db, book, book_update)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred while updating the book")

@router.delete("/{book_id}", status_code=204)
async def delete_book_endpoint(
    book_id: int,
    db: Session = Depends(get_session)
):
    """Remove a book from the library"""
    book = get_book(db, book_id)
    if not book:
        raise HTTPException(
            status_code=404,
            detail=f"Book with ID {book_id} not found"
        )
    
    # Check if book is currently borrowed
    if is_book_borrowed(book):
        raise HTTPException(
            status_code=400,
            detail="Cannot delete book that is currently borrowed"
        )
    
    delete_book(db, book)
    return None

@router.get("/{book_id}/availability")
async def check_book_availability_endpoint(
    book_id: int,
    db: Session = Depends(get_session)
):
    """Check availability status of a specific book"""
    book = get_book(db, book_id)
    if not book:
        raise HTTPException(
            status_code=404,
            detail=f"Book with ID {book_id} not found"
        )
    
    return check_book_availability(db, book)
