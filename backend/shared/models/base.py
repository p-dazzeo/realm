from sqlalchemy import Column, Integer, DateTime, String
from sqlalchemy.sql import func
from core.database import Base
import uuid

class BaseModel(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class UUIDMixin:
    uuid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4())) 