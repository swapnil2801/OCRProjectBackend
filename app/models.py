from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey, Text
from .database import Base
from sqlalchemy.orm import relationship
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(120), unique=True, index=True, nullable=False)
    email = Column(String(320), unique=True, index=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    history = relationship("History", back_populates="user")


class History(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    file_name = Column(String, nullable=False)
    scan_type = Column(String, nullable=False)
    extracted_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="history")