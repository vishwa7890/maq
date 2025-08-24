"""
User model and related functionality.
"""
from datetime import datetime
import random
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class User(Base):
    """User model representing application users."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    quai_id = Column(
        String(8), 
        unique=True, 
        nullable=False, 
        index=True, 
        default=lambda: f"quai{random.randint(100,999)}"
    )
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    phone_number = Column(String(15), nullable=True, index=True)
    hashed_password = Column(String, nullable=False)
    # User role: 'normal' or 'premium'
    role = Column(String(20), nullable=False, index=True, default="normal")
    # Track quotes usage for normal users (limit: 5)
    quotes_used = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    messages = relationship(
        "ChatMessageORM", 
        back_populates="user", 
        foreign_keys="[ChatMessageORM.user_id]", 
        cascade="all, delete-orphan"
    )
    chat_sessions = relationship(
        "ChatSessionORM", 
        back_populates="user", 
        foreign_keys="[ChatSessionORM.user_id]", 
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<User {self.username} ({self.quai_id})>"
