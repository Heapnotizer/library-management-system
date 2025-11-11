from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from .models import (
    UserCreate, UserUpdate, UserResponse, UserLogin, TokenResponse, UserRole
)
from .repository import (
    create_user, get_user_by_id,
    get_users, update_user, authenticate_user, delete_user
)
from ...db.session import get_session
from ...security.jwt_handler import create_access_token, verify_token
from ...security.password import verify_password
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()
security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_session)):
    """Dependency to get current user from JWT token"""
    try:
        token = credentials.credentials
        payload = verify_token(token)
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Token verification error: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


def require_admin(current_user = Depends(get_current_user)):
    """Dependency to require admin role"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register_endpoint(
    user_data: UserCreate,
    db: Session = Depends(get_session)
):
    """Register a new user"""
    try:
        user = create_user(db, user_data, role=UserRole.REGULAR)
        
        # Create access token
        access_token = create_access_token(data={"sub": user.id})
        
        return TokenResponse(
            access_token=access_token,
            user=UserResponse.model_validate(user)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred during registration")


@router.post("/login", response_model=TokenResponse)
async def login_endpoint(
    credentials: UserLogin,
    db: Session = Depends(get_session)
):
    """Login user and get access token"""
    try:
        user = authenticate_user(db, credentials.username, credentials.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # Create access token
        access_token = create_access_token(data={"sub": user.id})
        
        return TokenResponse(
            access_token=access_token,
            user=UserResponse.model_validate(user)
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred during login")


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_endpoint(
    user_id: int,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """Get user by ID (owner or admin can view)"""
    try:
        user = get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
        
        # Check if current user is the owner or admin
        if current_user.id != user_id and current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="You can only view your own profile")
        
        return UserResponse.model_validate(user)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.get("/", response_model=List[UserResponse])
async def get_users_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    role: Optional[UserRole] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_session),
    current_user = Depends(require_admin)
):
    """Get list of users (admin only)"""
    try:
        users = get_users(db, skip=skip, limit=limit, role=role, is_active=is_active)
        return [UserResponse.model_validate(user) for user in users]
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user_endpoint(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """Update user profile (owner or admin can update)"""
    try:
        user = get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
        
        # Check if current user is the owner or admin
        if current_user.id != user_id and current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="You can only update your own profile")
        
        # Non-admin users cannot update is_active or role - remove these fields from update
        if current_user.role != UserRole.ADMIN:
            # Create a copy of the update data excluding restricted fields
            update_dict = user_update.model_dump(exclude_unset=True)
            update_dict.pop('is_active', None)
            user_update = UserUpdate(**update_dict)
        
        updated_user = update_user(db, user, user_update)
        return UserResponse.model_validate(updated_user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.post("/{user_id}/change-password")
async def change_password_endpoint(
    user_id: int,
    old_password: str,
    new_password: str,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """Change user password"""
    try:
        # User can only change their own password unless they're admin
        if current_user.id != user_id and current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Cannot change another user's password")
        
        user = get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
        
        # If not admin, verify old password
        if current_user.role != UserRole.ADMIN:
            if not verify_password(old_password, user.hashed_password):
                raise HTTPException(status_code=400, detail="Invalid current password")
        
        update_user(db, user, UserUpdate(), new_password=new_password)
        return {"message": "Password updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.post("/{user_id}/role", response_model=UserResponse)
async def update_user_role_endpoint(
    user_id: int,
    new_role: UserRole,
    db: Session = Depends(get_session),
    current_user = Depends(require_admin)
):
    """Update user role (admin only)"""
    try:
        user = get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
        
        updated_user = update_user(db, user, new_role=new_role)
        return UserResponse.model_validate(updated_user)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.delete("/{user_id}", status_code=204)
async def delete_user_endpoint(
    user_id: int,
    db: Session = Depends(get_session),
    current_user = Depends(require_admin)
):
    """Delete user (admin only)"""
    try:
        user = get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
        
        delete_user(db, user)
        return None
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
