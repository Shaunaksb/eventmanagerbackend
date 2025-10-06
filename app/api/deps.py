from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.db.models.user import User, Role
from app.schemas.token import TokenPayload

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"/api/v1/auth/login"
)

async def get_db() -> Generator[AsyncSession, None, None]:
    async with AsyncSessionLocal() as session:
        yield session

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(reusable_oauth2)
) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = await db.get(User, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


async def get_current_user_from_token(
    db: AsyncSession, token: str
) -> Optional[User]:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        return None
    user = await db.get(User, token_data.sub)
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def is_finance(current_user: User = Depends(get_current_active_user)) -> bool:
    if current_user.role != Role.FINANCE:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return True


def is_event_manager(current_user: User = Depends(get_current_active_user)) -> bool:
    if current_user.role != Role.EVENT_MANAGER:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return True


def is_finance_or_event_manager(current_user: User = Depends(get_current_active_user)) -> bool:
    if current_user.role not in [Role.FINANCE, Role.EVENT_MANAGER]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return True
