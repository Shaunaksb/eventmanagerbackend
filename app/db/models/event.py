import enum
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum

from app.db.models.base import Base

class AudienceRole(str, enum.Enum):
    ALL = "all"
    CEO = "ceo"
    HR = "hr"
    FINANCE = "finance"
    EVENT_MANAGER = "event_manager"
    EMPLOYEE = "employee"

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255))
    date = Column(DateTime, nullable=False)
    budget = Column(Float, nullable=False)
    audience_role = Column(Enum(AudienceRole), default=AudienceRole.ALL, nullable=False)
