from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..db.session import get_db
from ..models.user import User, UserRole
from ..schemas.token import Token, UserCreate, UserInDB
from ..core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
    get_current_user,
)
from ..core.config import settings

router = APIRouter()

@router.post("/register", response_model=Token)
async def register(
    user_in: UserCreate, db: AsyncSession = Depends(get_db)
) -> Any:
    """Register a new user."""
    # Check if user already exists
    result = await db.execute(select(User).filter(User.email == user_in.email))
    if result.scalars().first() is not None:
        raise HTTPException(
            status_code=400,
            detail="Email already registered",
        )
    
    # Create new user
    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        role=UserRole.USER,
        is_active=True,
    )
    user.set_password(user_in.password)
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Generate access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """OAuth2 compatible token login."""
    # Get user from database
    result = await db.execute(select(User).filter(User.email == form_data.username))
    user = result.scalars().first()
    
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # Generate access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserInDB)
async def read_users_me(
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get current user."""
    return current_user
