from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Index

if TYPE_CHECKING:
    from ..books.models import Book

class AuthorBase(SQLModel):
    """Base Author model with shared fields"""
    name: str = Field(min_length=1, max_length=200)
    email: Optional[str] = Field(default=None, max_length=254)
    bio: Optional[str] = Field(default=None, max_length=2000)
    birth_date: Optional[datetime] = Field(default=None)
    nationality: Optional[str] = Field(default=None, max_length=100)
    website: Optional[str] = Field(default=None, max_length=500)

class Author(AuthorBase, table=True):
    """Author database model"""
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc)) 
    
    # Relationship with books (assuming you'll add this later)
    books: List["Book"] = Relationship(back_populates="author")
    
    # Add indexes for better query performance
    __table_args__ = (
        Index('idx_author_name', 'name'),                    # Index on name for search queries
        Index('idx_author_email', 'email'),                  # Index on email for uniqueness checks
        Index('idx_author_nationality', 'nationality'),      # Index for filtering by nationality
        Index('idx_author_name_nationality', 'name', 'nationality'),  # Composite index
    )

class AuthorCreate(AuthorBase):
    """Schema for creating a new Author"""
    pass

class AuthorUpdate(SQLModel):
    """Schema for updating an Author"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    email: Optional[str] = Field(default=None, max_length=254)
    bio: Optional[str] = Field(default=None, max_length=2000)
    birth_date: Optional[datetime] = Field(default=None)
    nationality: Optional[str] = Field(default=None, max_length=100)
    website: Optional[str] = Field(default=None, max_length=500)

class BookSummary(SQLModel):
    """Summary of book for author responses"""
    id: int
    title: str
    isbn: Optional[str] = None
    published_year: Optional[int] = None
    available_copies: int

class AuthorResponse(AuthorBase):
    """Schema for Author response"""
    id: int
    books: List[BookSummary] = []
    created_at: datetime
    updated_at: datetime