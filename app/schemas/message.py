from pydantic import BaseModel, field_validator
from datetime import datetime

from app.db.models.message import RecipientRole

class MessageBase(BaseModel):
    recipient_role: RecipientRole
    content: str

    @field_validator("recipient_role", mode="before")
    def ensure_uppercase_enum(cls, v):
        if isinstance(v, str):
            v = v.upper()
            return RecipientRole[v]  # convert to Enum
        return v

class MessageCreate(MessageBase):
    pass

class MessageRead(MessageBase):
    id: int
    sender_id: int
    timestamp: datetime

    class Config:
        from_attributes = True
