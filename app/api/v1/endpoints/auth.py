from datetime import timedelta
import logging
from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt
from pydantic import ValidationError

from app import schemas
from app.api import deps
from app.core import security
from app.db.models.user import User

router = APIRouter()


@router.post("/register", response_model=schemas.UserRead)
async def register(
    *, 
    db: AsyncSession = Depends(deps.get_db), 
    user_in: schemas.UserCreate
) -> User:
    hashed_password = security.get_password_hash(user_in.password)
    db_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_password,
        role=user_in.role,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


@router.post("/login", response_model=schemas.Token)
async def login(
    db: AsyncSession = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> schemas.Token:
    user = await db.execute(
        select(User).filter(User.username == form_data.username)
    )
    db_user = user.scalars().first()
    if not db_user or not security.verify_password(
        form_data.password, db_user.hashed_password
    ):
        raise HTTPException(
            status_code=400, detail="Incorrect email or password"
        )
    elif not db_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token_expires = timedelta(minutes=security.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            db_user.id, expires_delta=access_token_expires
        ),
        "refresh_token": security.create_refresh_token(db_user.id),
        "token_type": "bearer",
    }


@router.post("/refresh-token", response_model=schemas.Token)
async def refresh_token(
    db: AsyncSession = Depends(deps.get_db), 
    refresh_token: str = Body(...)
) -> schemas.Token:
    try:
        payload = jwt.decode(
            refresh_token, security.settings.SECRET_KEY, algorithms=[security.settings.ALGORITHM]
        )
        token_data = schemas.TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid refresh token",
        )
    user = await db.get(User, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    access_token_expires = timedelta(minutes=security.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }