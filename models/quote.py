"""
Quote model and related functionality.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON as JSONB
from .base import Base

class Quote(Base):
    """Quote model representing project quotes."""
    __tablename__ = "quotes"
    
    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String, nullable=False)
    project_name = Column(String, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    scope_of_work = Column(JSONB, nullable=False)
    timeline = Column(String, nullable=False)
    pricing = Column(JSONB, nullable=False)
    total = Column(Float, nullable=False)
    notes = Column(Text, default="")
    payment_terms = Column(String, default="50% advance, 50% upon completion")
    
    def __repr__(self):
        return f"<Quote {self.project_name} for {self.client_name} (${self.total})>"
