from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class Book(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    isbn: Optional[str] = None
    published_year: Optional[int] = None
    total_copies: int = 1
    available_copies: int = 1
    author_id: Optional[int] = Field(default=None, foreign_key="author.id")