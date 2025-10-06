import enum
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship

from app.db.models.base import Base

class RecipientRole(str, enum.Enum):
    ALL = "ALL"
    CEO = "CEO"
    HR = "HR"
    FINANCE = "FINANCE"
    EVENT_MANAGER = "EVENT_MANAGER"
    EMPLOYEE = "EMPLOYEE"
    ADMIN = "ADMIN"


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"))
    recipient_role = Column(
        Enum(
            RecipientRole,
            values_callable=lambda x: [e.value for e in x],  # store the Enum value
            native_enum=False  # store as VARCHAR, safer for cross-DB compatibility
        ),
        nullable=False
    )
    content = Column(String(255), nullable=False)
    timestamp = Column(DateTime, nullable=False)

    sender = relationship("User")
