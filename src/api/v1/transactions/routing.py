from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from .models import (
    TransactionCreate, TransactionUpdate, TransactionResponse
)
from .repository import (
    create_transaction, get_transaction_by_id, get_transactions_by_user,
    get_transactions_by_book, get_all_transactions, update_transaction,
    return_book, delete_transaction
)
from ...db.session import get_session
from ..users.routing import get_current_user
from ..users.models import UserRole

router = APIRouter()


def require_admin(current_user = Depends(get_current_user)):
    """Dependency to require admin role"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.post("", response_model=TransactionResponse, status_code=201)
async def create_transaction_endpoint(
    transaction_data: TransactionCreate,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """Create a new transaction (borrow a book) - Protected (All Users)"""
    try:
        transaction = create_transaction(db, transaction_data)
        return TransactionResponse.model_validate(transaction)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction_endpoint(
    transaction_id: int,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """Get transaction by ID - Protected (Owner or Admin)"""
    try:
        transaction = get_transaction_by_id(db, transaction_id)
        if not transaction:
            raise HTTPException(status_code=404, detail=f"Transaction with ID {transaction_id} not found")
        
        # Check authorization: user can only see own transactions, admins can see all
        if current_user.id != transaction.user_id and current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Cannot access another user's transaction")
        
        return TransactionResponse.model_validate(transaction)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.get("/user/{user_id}", response_model=List[TransactionResponse])
async def get_user_transactions_endpoint(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    is_returned: Optional[bool] = Query(None),
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """Get all transactions for a user - Protected (Owner or Admin)"""
    try:
        # Check authorization: user can only see own transactions, admins can see all
        if current_user.id != user_id and current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Cannot access another user's transactions")
        
        transactions = get_transactions_by_user(db, user_id, skip=skip, limit=limit, is_returned=is_returned)
        return [TransactionResponse.model_validate(t) for t in transactions]
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.get("/book/{book_id}", response_model=List[TransactionResponse])
async def get_book_transactions_endpoint(
    book_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    is_returned: Optional[bool] = Query(None),
    db: Session = Depends(get_session),
    current_user = Depends(require_admin)
):
    """Get all transactions for a book - Admin Only"""
    try:
        transactions = get_transactions_by_book(db, book_id, skip=skip, limit=limit, is_returned=is_returned)
        return [TransactionResponse.model_validate(t) for t in transactions]
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
 
  
@router.get("", response_model=List[TransactionResponse])
async def get_all_transactions_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    is_returned: Optional[bool] = Query(None),
    db: Session = Depends(get_session),
    current_user = Depends(require_admin)
):
    """Get all transactions - Admin Only"""
    try:
        transactions = get_all_transactions(db, skip=skip, limit=limit, is_returned=is_returned)
        return [TransactionResponse.model_validate(t) for t in transactions]
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.patch("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction_endpoint(
    transaction_id: int,
    transaction_update: TransactionUpdate,
    db: Session = Depends(get_session),
    current_user = Depends(require_admin)
):
    """Update a transaction - Admin Only"""
    try:
        transaction = get_transaction_by_id(db, transaction_id)
        if not transaction:
            raise HTTPException(status_code=404, detail=f"Transaction with ID {transaction_id} not found")
        
        updated_transaction = update_transaction(db, transaction, transaction_update)
        return TransactionResponse.model_validate(updated_transaction)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.post("/{transaction_id}/return", response_model=TransactionResponse)
async def return_book_endpoint(
    transaction_id: int,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """Mark a book as returned - Protected (Owner or Admin)"""
    try:
        transaction = get_transaction_by_id(db, transaction_id)
        if not transaction:
            raise HTTPException(status_code=404, detail=f"Transaction with ID {transaction_id} not found")
        
        # Check authorization: user can only return own books, admins can return any
        if current_user.id != transaction.user_id and current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Cannot return another user's book")
        
        transaction = return_book(db, transaction_id)
        return TransactionResponse.model_validate(transaction)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.delete("/{transaction_id}", status_code=204)
async def delete_transaction_endpoint(
    transaction_id: int,
    db: Session = Depends(get_session),
    current_user = Depends(require_admin)
):
    """Delete a transaction - Admin Only"""
    try: 
        transaction = get_transaction_by_id(db, transaction_id)
        if not transaction:
            raise HTTPException(status_code=404, detail=f"Transaction with ID {transaction_id} not found")
        
        delete_transaction(db, transaction)
        return None
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

