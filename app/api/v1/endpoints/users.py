from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.user import Role, User
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.api.deps import get_current_active_user, get_db
from app.core.security import get_password_hash, verify_password

router = APIRouter()

@router.get("/", response_model=List[UserRead])
async def read_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[User]:
    """
    Get all users.
    """
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    users = await db.execute(select(User))
    return users.scalars().all()

@router.post("/", response_model=UserRead)
async def create_user(
    *, 
    db: AsyncSession = Depends(get_db), 
    user_in: UserCreate
) -> User:
    """
    Create new user.
    """
    user = await db.execute(
        select(User).where(User.email == user_in.email)
    )
    if user.scalars().first():
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    hashed_password = get_password_hash(user_in.password)
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

@router.get("/me", response_model=UserRead)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get current user.
    """
    return current_user

@router.put("/me", response_model=UserRead)
async def update_user_me(
    *, 
    db: AsyncSession = Depends(get_db), 
    password: str = None,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Update own user.
    """
    if user_in.email and user_in.email != current_user.email:
        user = await db.execute(
            select(User).where(User.email == user_in.email)
        )
        if user.scalars().first():
            raise HTTPException(
                status_code=400,
                detail="The user with this username already exists in the system.",
            )
    if password:
        current_user.hashed_password = get_password_hash(password)
        
    user_data = user_in.dict(exclude_unset=True)
    for field in user_data:
        setattr(current_user, field, user_data[field])
        
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user

@router.get("/roles", response_model=List[str])
def get_roles():
    """
    Get all available user roles.
    """
    return [role.value.upper() for role in Role]

@router.get("/{user_id}", response_model=UserRead)
async def read_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get a specific user by id.
    """
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=UserRead)
async def update_user(
    *, 
    db: AsyncSession = Depends(get_db), 
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Update a user.
    """
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system",
        )
    if user_in.email and user_in.email != user.email:
        existing_user = await db.execute(
            select(User).where(User.email == user_in.email)
        )
        if existing_user.scalars().first():
            raise HTTPException(
                status_code=400,
                detail="The user with this username already exists in the system.",
            )
    user_data = user_in.dict(exclude_unset=True)
    for field in user_data:
        setattr(user, field, user_data[field])
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    *, 
    db: AsyncSession = Depends(get_db), 
    user_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a user.
    """
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system",
        )
    await db.delete(user)
    await db.commit()
    return {"ok": True}
