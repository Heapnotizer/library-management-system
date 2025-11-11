from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from .models import AuthorCreate, AuthorUpdate, AuthorResponse
from .repository import (
    create_author, get_author, get_author_by_email, get_authors,
    update_author, delete_author
)
from ...db.session import get_session

router = APIRouter()


@router.post("/", response_model=AuthorResponse, status_code=201)
async def create_author_endpoint(
    author_data: AuthorCreate,
    db: Session = Depends(get_session)
):
    """Create a new author"""
    try:
        # Check if author with same email already exists
        if author_data.email:
            existing_author = get_author_by_email(db, author_data.email)
            if existing_author:
                raise HTTPException(
                    status_code=400,
                    detail=f"Author with email {author_data.email} already exists"
                )
        
        # Create new author using CRUD function
        return create_author(db, author_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred while creating the author")


@router.get("/", response_model=List[AuthorResponse])
async def get_authors_endpoint(
    skip: int = Query(0, ge=0, description="Number of authors to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of authors to return"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    nationality: Optional[str] = Query(None, description="Filter by nationality"),
    db: Session = Depends(get_session)
):
    """Get list of authors with optional filtering and pagination"""
    try:
        return get_authors(
            db=db,
            skip=skip,
            limit=limit,
            search=search,
            nationality=nationality
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred while retrieving authors")


@router.get("/{author_id}", response_model=AuthorResponse)
async def get_author_endpoint(
    author_id: int,
    db: Session = Depends(get_session)
):
    """Get details of a specific author"""
    try:
        author = get_author(db, author_id)
        if not author:
            raise HTTPException(
                status_code=404,
                detail=f"Author with ID {author_id} not found"
            )
        return author
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred while retrieving the author")


@router.patch("/{author_id}", response_model=AuthorResponse)
async def update_author_endpoint(
    author_id: int,
    author_update: AuthorUpdate,
    db: Session = Depends(get_session)
):
    """Update author information"""
    try:
        author = get_author(db, author_id)
        if not author:
            raise HTTPException(
                status_code=404,
                detail=f"Author with ID {author_id} not found"
            )
        
        # Check if email is being updated and already exists
        if author_update.email and author_update.email != author.email:
            existing_author = get_author_by_email(db, author_update.email)
            if existing_author:
                raise HTTPException(
                    status_code=400,
                    detail=f"Author with email {author_update.email} already exists"
                )
        
        # Update using CRUD function
        return update_author(db, author, author_update)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred while updating the author")


@router.delete("/{author_id}", status_code=204)
async def delete_author_endpoint(
    author_id: int,
    db: Session = Depends(get_session)
):
    """Remove an author from the system"""
    try:
        author = get_author(db, author_id)
        if not author:
            raise HTTPException(
                status_code=404,
                detail=f"Author with ID {author_id} not found"
            )
        
        # Check if author has books
        if author.books:
            raise HTTPException(
                400,
                f"Cannot delete author with {len(author.books)} book(s). Delete or reassign the books first."
            )
        
        delete_author(db, author)
        return None
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred while deleting the author")