from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Index

if TYPE_CHECKING:
    from ..authors.models import Author

class BookBase(SQLModel):
    """Base Book model with shared fields"""
    title: str = Field(min_length=1, max_length=200)
    isbn: Optional[str] = Field(default=None, max_length=13, unique=True)
    published_year: Optional[int] = Field(default=None, ge=1000, le=2030)
    total_copies: int = Field(default=1, ge=1)
    available_copies: int = Field(default=1, ge=0)
    author_id: int = Field(foreign_key="author.id")
    description: Optional[str] = Field(default=None, max_length=1000)

class Book(BookBase, table=True):
    """Book database model"""
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    author: "Author" = Relationship(back_populates="books")
    
    # Add indexes for better query performance
    __table_args__ = (
        Index('idx_book_author_id', 'author_id'),   # Index on author_id for filtering by author
        Index('idx_book_title_author', 'title', 'author_id'),  # Composite index for title + author queries
        Index('idx_book_available_copies', 'available_copies'), # Index for availability filtering
    )

class BookCreate(BookBase):
    """Schema for creating a new book"""
    pass

class BookUpdate(SQLModel):
    """Schema for updating a book"""
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    isbn: Optional[str] = Field(default=None, max_length=13, unique=True)
    published_year: Optional[int] = Field(default=None, ge=1000, le=2030)
    total_copies: Optional[int] = Field(default=None, ge=1)
    available_copies: Optional[int] = Field(default=None, ge=0)
    author_id: Optional[int] = Field(default=None)
    description: Optional[str] = Field(default=None, max_length=1000)

class AuthorSummary(SQLModel):
    """Summary of author for book responses"""
    id: int
    name: str
    nationality: Optional[str] = None

class BookResponse(BookBase):
    """Schema for book response"""
    id: int
    author: Optional[AuthorSummary] = None
    created_at: datetime
    updated_at: datetime