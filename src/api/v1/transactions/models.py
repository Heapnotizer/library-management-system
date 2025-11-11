from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Index


class TransactionBase(SQLModel):
    """Base Transaction model with shared fields"""
    user_id: int = Field(foreign_key="user.id")
    book_id: int = Field(foreign_key="book.id")
    borrow_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    return_date: Optional[datetime] = Field(default=None)
    is_returned: bool = Field(default=False)


class Transaction(TransactionBase, table=True):
    """Transaction database model"""
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Add indexes for better query performance
    __table_args__ = (
        Index('idx_transaction_user_id', 'user_id'),
        Index('idx_transaction_book_id', 'book_id'),
        Index('idx_transaction_is_returned', 'is_returned'),
        Index('idx_transaction_borrow_date', 'borrow_date'),
    )


class TransactionCreate(SQLModel):
    """Schema for creating a new transaction"""
    user_id: int
    book_id: int
    borrow_date: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))


class TransactionUpdate(SQLModel):
    """Schema for updating a transaction"""
    return_date: Optional[datetime] = Field(default=None)
    is_returned: Optional[bool] = Field(default=None)


class TransactionResponse(TransactionBase):
    """Schema for transaction response"""
    id: int
    created_at: datetime
    updated_at: datetime
