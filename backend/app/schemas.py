from pydantic import BaseModel, Field, EmailStr
from typing import List, Dict, Any, Optional
from datetime import datetime

# --- User Schemas ---
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    phone_number: Optional[str] = Field(None, min_length=10, max_length=15, description="User's mobile number")
    # Optional role selection from UI; backend will validate and enforce allowed values
    role: str = Field(default="normal", description="User plan role: 'normal' or 'premium'")

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(UserBase):
    id: int
    quai_id: str
    created_at: datetime
    role: str = "normal"

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


class AnalysisPromptRequest(BaseModel):
    """Incoming payload for analysis prompt generation."""
    topic: str = Field(..., description="High-level topic or question the user wants to analyze")
    context: Optional[str] = Field(None, description="Additional business context, data, or goals")
    tone: Optional[str] = Field(None, description="Preferred tone (e.g., professional, concise, data-driven)")


class AnalysisPromptResponse(BaseModel):
    """Response payload containing generated analysis prompt."""
    prompt: str
    suggestions: Optional[List[str]] = None

# --- Quote Schemas ---
class QuoteItem(BaseModel):
    """Individual line item for a quotation."""
    description: str = Field(..., description="Description of the service/item")
    quantity: float = Field(1.0, description="Quantity of the item")
    unit: str = Field("hours", description="Unit of measurement (e.g., hours, items)")
    unit_price: float = Field(..., description="Price per unit in INR")
    
    class Config:
        json_schema_extra = {
            "example": {
                "description": "Frontend Development",
                "quantity": 40,
                "unit": "hours",
                "unit_price": 2500
            }
        }

class QuoteRequest(BaseModel):
    """Base quote request model for generating quotations."""
    client_name: str = Field(..., description="Name of the client")
    client_email: Optional[EmailStr] = Field(None, description="Client's email address")
    client_company: Optional[str] = Field(None, description="Client's company name")
    project_name: str = Field(..., description="Name of the project")
    project_description: str = Field(..., description="Detailed description of the project")
    project_type: str = Field(..., description="Type of the project (e.g., 'web', 'mobile', 'custom-software')")
    timeline: str = Field(..., description="Project timeline (e.g., '4 weeks', '3 months')")
    items: List[QuoteItem] = Field(..., description="List of line items for the quotation")
    tax_rate: float = Field(0.18, description="Tax rate as a decimal (e.g., 0.18 for 18%)")
    discount: float = Field(0.0, description="Discount amount in INR")
    notes: Optional[str] = Field(None, description="Additional notes or terms")
    
    class Config:
        json_schema_extra = {
            "example": {
                "client_name": "John Doe",
                "client_email": "john@example.com",
                "client_company": "Acme Corp",
                "project_name": "E-commerce Website",
                "project_description": "Development of a full-featured e-commerce platform",
                "project_type": "web",
                "timeline": "8 weeks",
                "items": [
                    {
                        "description": "Frontend Development",
                        "quantity": 120,
                        "unit": "hours",
                        "unit_price": 2500
                    },
                    {
                        "description": "Backend Development",
                        "quantity": 160,
                        "unit": "hours",
                        "unit_price": 3000
                    }
                ],
                "tax_rate": 0.18,
                "discount": 5000,
                "notes": "50% payment in advance, balance on completion"
            }
        }

class QuoteResponse(BaseModel):
    """Enhanced quote response with detailed breakdown."""
    quotation_id: str = Field(..., description="Unique identifier for the quotation")
    date_created: str = Field(..., description="Date when the quote was created")
    client: Dict[str, str] = Field(..., description="Client information")
    project: Dict[str, str] = Field(..., description="Project details")
    line_items: List[Dict[str, str]] = Field(..., description="Detailed line items")
    summary: Dict[str, str] = Field(..., description="Financial summary")
    terms: List[str] = Field(..., description="Terms and conditions")
    notes: str = Field("", description="Additional notes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "quotation_id": "QUO-123456",
                "date_created": "2023-10-15",
                "client": {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "company": "Acme Corp"
                },
                "project": {
                    "name": "E-commerce Website",
                    "description": "Development of a full-featured e-commerce platform",
                    "timeline": "8 weeks"
                },
                "line_items": [
                    {
                        "description": "Frontend Development",
                        "quantity": "120",
                        "unit": "hours",
                        "unit_price": "2,500.00",
                        "total": "300,000.00"
                    },
                    {
                        "description": "Backend Development",
                        "quantity": "160",
                        "unit": "hours",
                        "unit_price": "3,000.00",
                        "total": "480,000.00"
                    }
                ],
                "summary": {
                    "subtotal": "780,000.00",
                    "tax_rate": "18%",
                    "tax_amount": "140,400.00",
                    "discount": "5,000.00",
                    "total": "915,400.00",
                    "currency": "INR"
                },
                "terms": [
                    "50% advance payment required to begin work",
                    "Balance payment due upon project completion",
                    "Prices valid for 30 days"
                ],
                "notes": "Additional customization available upon request"
            }
        }

class PremiumQuotationRequest(QuoteRequest):
    """Enhanced quote request for premium users with additional features."""
    include_watermark: bool = Field(False, description="Whether to include watermark in exports")
    custom_logo_url: Optional[str] = Field(None, description="URL to custom logo for branding")
    custom_terms: Optional[List[str]] = Field(None, description="Custom terms and conditions")
    
    class Config:
        json_schema_extra = {
            "example": {
                **QuoteRequest.Config.json_schema_extra["example"],
                "include_watermark": False,
                "custom_logo_url": "https://example.com/logo.png",
                "custom_terms": [
                    "Additional support included for 30 days post-delivery",
                    "Source code ownership transferred upon final payment"
                ]
            }
        }

class QuoteInteraction(BaseModel):
    """Tracks user interactions with quotes."""
    quote_id: str = Field(..., description="Unique identifier for the quote")
    interaction_type: str = Field(..., 
        description="Type of interaction (e.g., 'download', 'edit', 'ignore', 'share')")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Additional metadata about the interaction"
    )
    user_role: str = Field(
        "normal", 
        description="User's role at the time of interaction (normal/premium)"
    )
    features_used: Optional[List[str]] = Field(
        None,
        description="Premium features used during this interaction"
    )

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
