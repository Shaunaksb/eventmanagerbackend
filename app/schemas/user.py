from pydantic import BaseModel, EmailStr
from typing import Optional

from app.db.models.user import Role

class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: Role

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    pass

class UserRead(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True
