import enum
from sqlalchemy import Column, Integer, String, Boolean, Enum

from app.db.models.base import Base

class Role(str, enum.Enum):
    ADMIN = "admin"
    CEO = "ceo"
    HR = "hr"
    FINANCE = "finance"
    EVENT_MANAGER = "event_manager"
    EMPLOYEE = "employee"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(Role), default=Role.EMPLOYEE, nullable=False)
    is_active = Column(Boolean, default=True)
