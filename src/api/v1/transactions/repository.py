from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import List, Optional
from datetime import datetime, timezone

from .models import Transaction, TransactionCreate, TransactionUpdate


def create_transaction(db: Session, transaction_data: TransactionCreate) -> Transaction:
    """Create a new transaction (borrow request)
    
    Validates that the book has available copies before allowing the borrow
    """
    try: 
        from ..books.repository import calculate_available_copies
        
        # Check if book exists and has available copies
        available = calculate_available_copies(db, transaction_data.book_id)
        if available <= 0:
            raise ValueError("No available copies of this book to borrow")
        
        db_transaction = Transaction(
            user_id=transaction_data.user_id,
            book_id=transaction_data.book_id,
            borrow_date=transaction_data.borrow_date,
            is_returned=False
        )
        db.add(db_transaction)
        db.commit()
        db.refresh(db_transaction)
        return db_transaction
    except IntegrityError as e:
        db.rollback()
        print(e)
        if "user_id" in str(e):
            raise ValueError("User not found")
        if "book_id" in str(e):
            raise ValueError("Book not found")
        raise ValueError(f"Data integrity error: {str(e)}")
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError(f"Database error while creating transaction: {str(e)}")


def get_transaction_by_id(db: Session, transaction_id: int) -> Optional[Transaction]:
    """Get transaction by ID"""
    try:
        return db.query(Transaction).filter(Transaction.id == transaction_id).first()
    except SQLAlchemyError as e:
        raise RuntimeError(f"Database error while retrieving transaction: {str(e)}")


def get_transactions_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 10, is_returned: Optional[bool] = None) -> List[Transaction]:
    """Get all transactions for a user"""
    try:
        query = db.query(Transaction).filter(Transaction.user_id == user_id)
        
        if is_returned is not None:
            query = query.filter(Transaction.is_returned == is_returned)
        
        return query.offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        raise RuntimeError(f"Database error while retrieving transactions: {str(e)}")


def get_transactions_by_book(db: Session, book_id: int, skip: int = 0, limit: int = 10, is_returned: Optional[bool] = None) -> List[Transaction]:
    """Get all transactions for a book"""
    try:
        query = db.query(Transaction).filter(Transaction.book_id == book_id)
        
        if is_returned is not None:
            query = query.filter(Transaction.is_returned == is_returned)
        
        return query.offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        raise RuntimeError(f"Database error while retrieving transactions: {str(e)}")


def get_all_transactions(db: Session, skip: int = 0, limit: int = 10, is_returned: Optional[bool] = None) -> List[Transaction]:
    """Get all transactions with optional filtering"""
    try:
        query = db.query(Transaction)
        
        if is_returned is not None:
            query = query.filter(Transaction.is_returned == is_returned)
        
        return query.offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        raise RuntimeError(f"Database error while retrieving transactions: {str(e)}")


def update_transaction(db: Session, transaction: Transaction, transaction_update: TransactionUpdate) -> Transaction:
    """Update transaction"""
    try:
        update_data = transaction_update.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(transaction, field, value)
        
        transaction.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(transaction)
        
        return transaction
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError(f"Database error while updating transaction: {str(e)}")


def return_book(db: Session, transaction_id: int) -> Transaction:
    """Mark a book as returned"""
    try:
        transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not transaction:
            raise ValueError("Transaction not found")
        
        if transaction.is_returned:
            raise ValueError("Book already returned")
        
        transaction.return_date = datetime.now(timezone.utc)
        transaction.is_returned = True
        transaction.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(transaction)
        
        return transaction
    except ValueError:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError(f"Database error while returning book: {str(e)}")


def delete_transaction(db: Session, transaction: Transaction) -> None:
    """Delete a transaction"""
    try:
        db.delete(transaction)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError(f"Database error while deleting transaction: {str(e)}")
