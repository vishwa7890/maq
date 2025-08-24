"""
Interaction models for tracking user interactions with quotes and other entities.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON as JSONB
from sqlalchemy.orm import relationship
from .base import Base

class QuoteInteractionORM(Base):
    """Model for tracking user interactions with quotes."""
    __tablename__ = "quote_interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    quai_id = Column(String(8), ForeignKey('users.quai_id'), nullable=False)
    interaction_type = Column(String, nullable=False)
    interaction_metadata = Column(JSONB, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    
    def __repr__(self):
        return f"<QuoteInteraction {self.interaction_type} on quote {self.quote_id} by user {self.quai_id}>"
