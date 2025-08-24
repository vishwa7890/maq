"""
Chat-related models including ChatSession, ChatMessage, and Document models.
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey, 
    JSON as JSONB, Float
)
from sqlalchemy.orm import relationship
from .base import Base

class ChatSessionORM(Base):
    """Chat session model representing a conversation."""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_uuid = Column(
        String(36), 
        unique=True, 
        nullable=False, 
        index=True, 
        default=lambda: str(uuid.uuid4())
    )
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    quai_id = Column(String(8), ForeignKey('users.quai_id'), nullable=False)
    title = Column(String(100), default="New Chat")
    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    session_metadata = Column(JSONB, default=dict, nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    messages = relationship(
        "ChatMessageORM", 
        back_populates="session", 
        cascade="all, delete-orphan",
        order_by="asc(ChatMessageORM.timestamp)"
    )
    documents = relationship(
        "DocumentORM", 
        back_populates="session", 
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<ChatSession {self.id} - {self.title}>"


class ChatMessageORM(Base):
    """Chat message model representing messages in a conversation."""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    message_uuid = Column(
        String(36), 
        unique=True, 
        nullable=False, 
        index=True, 
        default=lambda: str(uuid.uuid4())
    )
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    quai_id = Column(String(8), ForeignKey('users.quai_id'), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    session_id = Column(
        Integer, 
        ForeignKey('chat_sessions.id', ondelete='CASCADE'), 
        nullable=False
    )
    meta = Column('metadata', JSONB, default=dict, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="messages", foreign_keys=[user_id])
    session = relationship(
        "ChatSessionORM", 
        back_populates="messages", 
        foreign_keys=[session_id],
        single_parent=True
    )
    
    @property
    def chat_id(self):
        return self.message_uuid
    
    @chat_id.setter
    def chat_id(self, value):
        self.message_uuid = value
    
    def to_dict(self):
        return {
            "id": self.id,
            "message_uuid": self.message_uuid,
            "user_id": self.user_id,
            "quai_id": self.quai_id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "meta": self.meta or {}
        }
    
    def __repr__(self):
        return f"<ChatMessage {self.role}: {self.content[:50]}...>"


class DocumentORM(Base):
    """Document model for uploaded files."""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    document_uuid = Column(
        String(36), 
        unique=True, 
        nullable=False, 
        index=True, 
        default=lambda: str(uuid.uuid4())
    )
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    session_id = Column(Integer, ForeignKey('chat_sessions.id', ondelete='CASCADE'), nullable=True)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(512), nullable=False)
    filetype = Column(String(50), nullable=False)
    filesize = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, index=True)
    processed = Column(Boolean, default=False, index=True)
    processing_error = Column(Text, nullable=True)
    extracted_text = Column(Text, nullable=True)
    extracted_tables = Column(JSONB, nullable=True)
    page_count = Column(Integer, nullable=True)
    meta = Column('metadata', JSONB, default=dict, nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    session = relationship(
        "ChatSessionORM", 
        foreign_keys=[session_id],
        back_populates="documents"
    )
    comparisons = relationship(
        "PDFComparisonORM", 
        back_populates="document", 
        cascade="all, delete-orphan"
    )
    
    def to_dict(self):
        return {
            "id": self.id,
            "document_uuid": self.document_uuid,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "filename": self.filename,
            "filepath": self.filepath,
            "filetype": self.filetype,
            "filesize": self.filesize,
            "uploaded_at": self.uploaded_at.isoformat(),
            "processed": self.processed,
            "processing_error": self.processing_error,
            "page_count": self.page_count,
            "meta": self.meta or {}
        }
    
    def __repr__(self):
        return f"<Document {self.filename} ({self.filetype}, {self.filesize} bytes)>"


class PDFComparisonORM(Base):
    """PDF comparison model for storing comparison results."""
    __tablename__ = "pdf_comparisons"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    chat_id = Column(Integer, ForeignKey('chat_sessions.id'), nullable=False)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    estimation_json = Column(JSONB, nullable=False)
    comparison_score = Column(Float, nullable=False)
    mismatch_details = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    chat_session = relationship("ChatSessionORM", foreign_keys=[chat_id])
    document = relationship("DocumentORM", back_populates="comparisons")
    
    def __repr__(self):
        return f"<PDFComparison {self.id} - Score: {self.comparison_score}>"
