from pydantic import BaseModel, Field, EmailStr
from typing import List, Dict, Any, Optional
from datetime import datetime

# --- User Schemas ---
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    phone_number: str = Field(..., min_length=10, max_length=15, description="User's mobile number")

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(UserBase):
    id: int
    quai_id: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- Chat Session Schemas ---
class ChatSessionCreate(BaseModel):
    title: str = "New Chat"
    metadata: Optional[Dict[str, Any]] = None
    is_archived: bool = False

class ChatSessionUpdate(BaseModel):
    title: Optional[str] = None
    is_archived: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None

class ChatSessionResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    is_archived: bool
    message_count: int
    metadata: Dict[str, Any] = {}

# --- Chat Message Schemas ---
class ChatMessageCreate(BaseModel):
    role: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

class ChatMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    timestamp: str
    metadata: Dict[str, Any] = {}

class ChatRequest(BaseModel):
    role: str = "user"
    content: str
    chat_id: Optional[str] = None  # Session UUID to link messages to sessions
    history: List[Dict[str, str]] = []

# --- Quote Schemas ---
class QuoteRequest(BaseModel):
    client_name: str = Field(..., description="Name of the client")
    project_type: str = Field(..., description="Type of the software/project to be quoted")
    user_input: str = Field(..., description="Raw description from the user about the project requirements")

class QuoteResponse(BaseModel):
    client_name: str = Field(..., description="Name of the client")
    project_name: str = Field(..., description="Title of the project")
    date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"), description="Quote date")
    scope_of_work: Dict[str, List[str]] = Field(..., description="Detailed scope of work with phases and activities")
    timeline: str = Field(..., description="Estimated project timeline")
    pricing: Dict[str, float] = Field(..., description="Itemized pricing in INR")
    total: float = Field(..., description="Total quote amount")
    notes: str = Field(default="", description="Additional terms and conditions")
    payment_terms: str = Field(default="50% advance, 50% upon completion", description="Payment schedule")

class QuoteInteraction(BaseModel):
    quote_id: str = Field(..., description="Unique identifier for the quote")
    interaction_type: str = Field(..., description="Type of interaction (e.g., 'download', 'edit', 'ignore', 'share')")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the interaction")

# --- Document and Comparison Schemas ---
class SearchDocument(BaseModel):
    id: str
    text: str
    metadata: Dict[str, Any] = {}

class PDFUploadResponse(BaseModel):
    document_id: int
    filename: str
    filesize: int
    processed: bool
    message: str

class ComparisonResult(BaseModel):
    document_id: int
    filename: str
    match_score: float
    closest_matches: List[Dict[str, str]]
    mismatches: List[str]
    suggestions: List[str]

class PDFComparisonRequest(BaseModel):
    document_id: int
    estimation_data: Dict[str, Any]
    chat_id: int
