from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from app.db.models.event import AudienceRole

class EventBase(BaseModel):
    name: str
    description: Optional[str] = None
    date: datetime
    budget: float
    audience_role: AudienceRole

class EventCreate(EventBase):
    pass

class EventUpdate(EventBase):
    pass

class EventRead(EventBase):
    id: int

    class Config:
        from_attributes = True
