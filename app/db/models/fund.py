from sqlalchemy import Column, Integer, Float

from app.db.models.base import Base

class Fund(Base):
    __tablename__ = "funds"

    id = Column(Integer, primary_key=True, index=True)
    balance = Column(Float, nullable=False)
