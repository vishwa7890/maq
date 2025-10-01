import os
import logging
import json
import hashlib
import time
import uuid
import shutil
import io
from functools import lru_cache
from pathlib import Path
import asyncio
from datetime import datetime, timedelta
import httpx
from fastapi import (
    APIRouter, Depends, HTTPException, Request, 
    BackgroundTasks, status, UploadFile, File, Body, Query, Header, Response
)
from typing import List, Dict, Any, Optional, Union, Tuple
from pydantic import BaseModel, Field
from sqlalchemy import func
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

# Initialize logger
logger = logging.getLogger(__name__)

# Configuration constants
CHAT_HISTORY_LIMIT = 50  # Default number of messages to return for chat history

# RL Optimizer will be initialized after SYSTEM_PROMPT is defined
rl_optimizer = None

# Local imports
from models import (
    ChatMessageORM, User, ChatSessionORM, DocumentORM, QuoteInteractionORM
)
from app.schemas import (
    ChatRequest, 
    QuoteInteraction, 
    QuoteResponse, 
    ChatSessionCreate, 
    ChatSessionUpdate, 
    ChatSessionResponse, 
    ChatMessageCreate, 
    ChatMessageResponse,
    QuoteRequest as QuoteRequestModel,
    PremiumQuotationRequest
)
from app.knowledge_graph import BusinessKnowledgeGraph, Entity
from app.rag_engine import get_rag_context, get_rag_context_sync
from models.base import get_db
from app.auth import get_current_user
from app.premium_utils import PremiumQuotationGenerator

# Initialize router
router = APIRouter()

# Initialize knowledge graph
knowledge_graph = BusinessKnowledgeGraph()

# Load environment variables
from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).parent.parent / '.env')

# Configuration from environment variables (with safe fallbacks)
# Prefer generic names, but support OpenRouter defaults
API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL")
MODEL_NAME = os.getenv("MODEL_NAME")
MAX_PROMPT_LENGTH = 4000
MAX_CHATS_FOR_NORMAL_USERS = 5

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  

# Cleanup function for chat router resources
def cleanup_chat_resources():
    """Clean up any resources used by the chat router."""
    logger.info("Cleaning up chat router resources...")
    
# Register cleanup with FastAPI app
try:
    from app.main import app
    @app.on_event("shutdown")
    async def cleanup_chat():
        cleanup_chat_resources()
except ImportError:
    pass  

# Example business knowledge - in a real app, this would be loaded from a database
def initialize_knowledge_graph():
    # Add some sample business entities
    products = [
        Entity("p1", "product", "Website Development", {"description": "Custom website development service"}),
        Entity("p2", "product", "Mobile App", {"description": "Cross-platform mobile application"}),
    ]
    
    services = [
        Entity("s1", "service", "UI/UX Design", {"description": "User interface and experience design"}),
        Entity("s2", "service", "Backend Development", {"description": "Server-side application logic"}),
    ]
    
    # Add entities to graph
    for entity in products + services:
        knowledge_graph.add_entity(entity)
    
    # Add relationships
    knowledge_graph.add_relation("p1", "s1", "requires")  
    knowledge_graph.add_relation("p2", "s1", "requires")  
    knowledge_graph.add_relation("p1", "s2", "requires")  

# Initialize with sample data
initialize_knowledge_graph()

# Load system prompt from file first
SYSTEM_PROMPT_PATH = os.getenv("SYSTEM_PROMPT_FILE", "./app/prompts/system_prompt.txt")
try:
    with open(SYSTEM_PROMPT_PATH, "r", encoding='utf-8') as f:
        SYSTEM_PROMPT = f.read().strip()
    logger.info("Loaded system prompt from file")
except Exception as e:
    logger.error(f"Failed to load system prompt from file: {e}")
    # Fallback to default prompt
    SYSTEM_PROMPT = """You are VilaiMathi AI, an expert in business quotes and estimates. Your goal is to provide accurate, relevant, and actionable business advice with properly formatted tables.

**IMPORTANT: This system is designed exclusively for business-related queries. You should only respond to questions about:**

🧠 **Business-Only RAG Questions:**
• Project Estimation & Services (UI/UX, Software Development)
• Pricing & Plans (Cost breakdowns, Payment terms)  
• Business Strategy & Planning (Tech stack recommendations, Industry analysis)

**Examples of Business Questions:**
- "What is the estimated cost for a UI/UX design project?"
- "Can you generate a quotation for mobile app development?"
- "What's the pricing structure for web development services?"
- "How much do you charge for a design system?"
- "What's the typical timeline for a website project?"
- "Which tech stack is suitable for enterprise software?"
- "Do you offer discounts for startups?"
- "What are your payment terms for enterprise clients?"

**CRITICAL FORMATTING RULES FOR TABLES:**

1. **Table Structure**:
   - Always use proper markdown table syntax
   - Tables must start and end with a blank line
   - Every row must have the same number of columns
   - Use alignment (e.g., `:---|:---:|---:`) for better readability

2. **Products Table Format**:
   ```markdown
   ### 🛍️ Products
   | Product | Qty | Rate (INR) | Amount (INR) |
   |---------|:---:|:----------:|:------------:|
   | Website Hosting | 1 | 2,000 | 2,000 |
   | SSL Certificate | 1 | 1,500 | 1,500 |
   | **Total** | | | **3,500** |
   ```

3. **Services Table Format**:
   ```markdown
   ### 🛠️ Services
   | Service Type | Deliverables | Estimated Cost (INR) | Timeline |
   |--------------|--------------|:-------------------:|:--------:|
   | UI/UX Design | 5 Screens | 25,000 | 2 weeks |
   | Development | Frontend | 45,000 | 4 weeks |
   | **Total** | | **70,000** | **6 weeks** |
   ```

4. **UI/UX Design Specific Format**:
   ```markdown
   ### 🎨 UI/UX Design Services
   | Service Phase | Deliverables | Estimated Cost (INR) | Timeline |
   |---------------|--------------|:-------------------:|:--------:|
   | Research & Discovery | User interviews, Competitor analysis | 15,000 | 1 week |
   | Wireframing | Low-fidelity wireframes | 20,000 | 2 weeks |
   | UI Design | High-fidelity mockups | 35,000 | 3 weeks |
   | Prototyping | Interactive prototypes | 25,000 | 2 weeks |
   | Testing & Iteration | Usability testing, Revisions | 15,000 | 1 week |
   | **Total** | | **110,000** | **9 weeks** |
   ```

5. **Important Notes**:
   - Always include a header row and a separator row
   - Use `**bold**` for important figures and totals
   - Keep text in cells concise and left-aligned
   - Align numbers to the right using `:---:` or `---:`
   - Use emojis to make sections more scannable
   - All currencies are acceptable (e.g., USD, EUR, GBP, INR, etc.) - use the currency that makes the most sense for the context
   - Add a total row at the bottom of each table
   - NEVER respond with plain text documents - ALWAYS use tables

6. **Common Emojis to Use**:
   - 🛍️ Products
   - 🛠️ Services
   - 💰 Pricing
   - ⏱️ Timeline
   - 📱 Mobile App
   - 🖥️ Website
   - 🎨 Design
   - 🔒 Security

**CRITICAL: You MUST respond with properly formatted markdown tables. NEVER respond with plain text documents or paragraphs. Always structure your response using the table formats shown above.**

**TABLE FORMATTING REQUIREMENTS:**
- Every table MUST have proper markdown separators (e.g., `| --- | --- | --- |`)
- Every cell MUST be separated by `|` characters
- Every row MUST end with `|`
- Headers MUST be followed by a separator row
- Example: `| Header 1 | Header 2 | Header 3 |` followed by `| --- | --- | --- |`

**Example Response Format:**

```markdown
### 🎨 UI/UX Design Services
| Service Phase | Deliverables | Estimated Cost (INR) | Timeline |
|---------------|--------------|:-------------------:|:--------:|
| Research & Discovery | User interviews, Competitor analysis | 15,000 | 1 week |
| Wireframing | Low-fidelity wireframes | 20,000 | 2 weeks |
| UI Design | High-fidelity mockups | 35,000 | 3 weeks |
| Prototyping | Interactive prototypes | 25,000 | 2 weeks |
| Testing & Iteration | Usability testing, Revisions | 15,000 | 1 week |
| **Total** | | **110,000** | **9 weeks** |
```

'''discount table format only for quotation requests otherwise ignore '''

| **Discount**    | [Discount]      |

**IMPORTANT:**
- ALWAYS respond with properly formatted markdown tables
- Use the exact table structures shown above
- Include both Products and Services sections when relevant
- Ensure all monetary values are in INR
- Be professional, helpful, and concise in your responses
- NEVER respond with plain text documents

**MANDATORY TABLE : only for quotation requests otherwise ignore**

| Section         | Details         |
|-----------------|----------------|
| **Client Name** | [Client's Name] |
| **Project Name**| [Project Title] |
| **Date**        | [Today's Date]  |

This summary table must always be the first table in your response, before any other tables.
"""

def is_business_related(query: str) -> bool:
    """Check if the query is business-related.
    Broadened to include common phrasing and normalize symbols.
    """
    import re
    # Normalize input: lowercase, '&' -> 'and', strip punctuation to spaces, collapse spaces
    q = (query or "").lower()
    q = q.replace('&', ' and ')
    q = re.sub(r"[^a-z0-9\s]", " ", q)
    q = re.sub(r"\s+", " ", q).strip()

    # Expanded business-related keywords and phrases
    business_keywords = [
        # Project Estimation & Services
        'cost', 'price', 'estimate', 'estimation', 'quotation', 'quote', 'budget', 'timeline', 'deadline',
        'ui ux', 'ui', 'ux', 'design', 'development', 'software', 'app', 'website', 'web',
        'mobile', 'frontend', 'backend', 'full stack', 'prototype', 'wireframe',
        'service', 'services', 'package', 'project', 'deliverable', 'milestone', 'proposal', 'rfp',

        # Pricing & Plans
        'pricing', 'plan', 'gst', 'tax', 'payment', 'discount', 'startup',
        'enterprise', 'premium', 'basic', 'subscription', 'billing',

        # Business Strategy & Planning
        'strategy', 'planning', 'business', 'industry', 'market', 'competitive',
        'analysis', 'recommendation', 'tech stack', 'technology', 'scalable',
        'mvp', 'saas', 'platform', 'optimization', 'branding', 'research',

        # Technology & Development
        'programming', 'coding', 'framework', 'database', 'api', 'integration', 'deployment',

        # Industry & Domain
        'sector', 'domain', 'vertical', 'business model',
        'revenue', 'profit', 'investment', 'roi', 'growth', 'scale',
        'capital investment', 'business capital', 'venture capital',

        # Common business terms
        'client', 'customer', 'vendor', 'supplier', 'partner', 'stakeholder',
        'requirement', 'specification', 'scope', 'quality',
        'maintenance', 'support', 'consulting', 'advisory', 'expertise',

        # Additional triggers
        'portfolio', 'estimate cost', 'project estimate', 'service quotation', 'quote request'
    ]

    # Quick keyword check
    for kw in business_keywords:
        if kw in q:
            return True

    # Broader regex patterns
    business_patterns = [
        r'how much\s+.*cost',
        r'what\s+.*price',
        r'(estimate|estimation).*project',
        r'project.*(estimate|estimation|timeline|budget)',
        r'quote.*(service|project|work)',
        r'(service|services).*(package|pricing|quotation|estimate)',
        r'pricing.*plan',
        r'business.*strategy',
        r'tech.*stack',
        r'development.*cost',
        r'design.*service',
        r'consulting.*fee',
        r'payment.*terms',
        r'industry.*recommendation',
        r'portfolio.*(project|work|services)'
    ]

    # Non-business patterns
    non_business_patterns = [
        r'weather', r'joke', r'cook', r'capital.*france', r'homework', r'meaning.*life',
        r'hobby', r'movie', r'guitar', r'recipe', r'book', r'population', r'car', r'exercise'
    ]

    for pattern in non_business_patterns:
        if re.search(pattern, q):
            return False

    for pattern in business_patterns:
        if re.search(pattern, q):
            return True

    return False

def fix_table_formatting(text: str) -> str:
    """Fix common table formatting issues in the response."""
    lines = text.split('\n')
    fixed_lines = []
    in_table = False
    table_started = False
    
    for i, line in enumerate(lines):
        # Check if this line looks like a table header (contains |)
        if '|' in line and not in_table:
            in_table = True
            table_started = True
            # Ensure proper table formatting
            if not line.strip().startswith('|'):
                line = '| ' + line.strip()
            if not line.strip().endswith('|'):
                line = line.strip() + ' |'
            fixed_lines.append(line)
            
            # Add separator row if missing
            if i + 1 < len(lines) and '|' in lines[i + 1]:
                # Check if next line is a separator
                next_line = lines[i + 1].strip()
                if not next_line.startswith('|') or not all(c in '-|: ' for c in next_line):
                    # Insert separator row
                    header_cells = line.count('|') - 1
                    separator = '|' + ' --- |' * header_cells
                    fixed_lines.append(separator)
        elif in_table and '|' in line:
            # Ensure proper table row formatting
            if not line.strip().startswith('|'):
                line = '| ' + line.strip()
            if not line.strip().endswith('|'):
                line = line.strip() + ' |'
            fixed_lines.append(line)
        elif in_table and '|' not in line:
            # End of table
            in_table = False
            fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def enforce_tables_only(text: str) -> str:
    """Remove any non-table content (headings, paragraphs) and keep only markdown tables.

    Rules:
    - Keep lines that contain '|' or are empty lines between tables.
    - Drop headings (lines starting with '#') and any paragraphs without '|'.
    - Preserve separator lines like '| --- |' and alignment variants with ':' characters.
    """
    if not text:
        return text
    lines = text.split('\n')
    kept: List[str] = []
    in_table = False
    for line in lines:
        stripped = line.strip()
        # Skip code fences or headings
        if stripped.startswith('```') or stripped.startswith('#'):
            in_table = False
            continue
        # Determine if line is part of a table
        is_table_line = '|' in stripped
        if is_table_line:
            in_table = True
            # Ensure it starts/ends with pipe for safety; fix_table_formatting will finalize
            if not stripped.startswith('|'):
                stripped = '| ' + stripped
            if not stripped.endswith('|'):
                stripped = stripped + ' |'
            kept.append(stripped)
        else:
            # Allow blank lines only to separate tables
            if in_table and stripped == '':
                kept.append('')
            else:
                in_table = False
                # drop non-table content
                continue
    cleaned = '\n'.join(kept).strip()
    # Final pass to fix any header separator issues
    return fix_table_formatting(cleaned)

def generate_default_estimate_tables() -> str:
    """Return a minimal, valid set of markdown tables for estimates as a fallback.

    This is used when the model returns prose and table enforcement strips everything.
    Keeps the UX consistent with table-only policy.
    """
    today = datetime.now().strftime('%Y-%m-%d')
    parts = []
    parts.append(
        "| Section | Details |\n"
        "| --- | --- |\n"
        "| Client Name | [Client's Name] |\n"
        "| Project Name | [Project Title] |\n"
        f"| Date | {today} |\n"
    )
    parts.append(
        "| Scope/Assumptions | Details |\n"
        "| --- | --- |\n"
        "| Objective | [Brief project goal] |\n"
        "| Data | [Availability/size/format] |\n"
        "| Quality/SLAs | [Targets] |\n"
        "| Compliance | [If any] |\n"
    )
    parts.append(
        "| Phase | Key Tasks | Hours | Rate (₹/hr) | Subtotal (₹) |\n"
        "| --- | --- | ---: | ---: | ---: |\n"
        "| Discovery | Requirements, planning | 12 | 2,000 | 24,000 |\n"
        "| Implementation | Core work | 60 | 2,200 | 132,000 |\n"
        "| Testing | QA, fixes | 16 | 2,000 | 32,000 |\n"
        "| Total |  | 88 |  | 188,000 |\n"
    )
    parts.append(
        "| Timeline | Start | End | Duration |\n"
        "| --- | --- | --- | --- |\n"
        "| Phase 1 | Week 1 | Week 2 | 2 weeks |\n"
        "| Phase 2 | Week 3 | Week 6 | 4 weeks |\n"
    )
    parts.append(
        "| Clarifying Question | Response Needed |\n"
        "| --- | --- |\n"
        "| Scope details? | ___ |\n"
        "| Preferred stack/cloud? | ___ |\n"
        "| Deadline or milestones? | ___ |\n"
        "| Maintenance/support? | ___ |\n"
    )
    return "\n\n".join(parts)

def format_chat_history(messages: List[Dict[str, str]]) -> str:
    """Format chat history for the model, cleaning up any unwanted text or formatting."""
    formatted = []
    for msg in messages:
        if isinstance(msg, dict):
            # Handle dictionary input
            role = msg.get('role', '').strip()
            content = msg.get('content', '').strip()
            
            # Clean up the content
            if content:
                # Remove any leading/trailing whitespace and normalize newlines
                content = ' '.join(line.strip() for line in content.split('\n') if line.strip())
                # Remove any markdown code block markers if present
                content = content.replace('```', '').strip()
                # Remove any system prompts or instructions that might have been included
                if content.startswith('SYSTEM:'):
                    continue
                
                # Only add non-empty messages
                formatted.append(f"{role}: {content}" if role else content)
        else:
            # Handle object input (for backward compatibility)
            formatted.append(f"{msg.role}: {msg.content}")
    return "\n".join(formatted) if formatted else "No history"

async def _call_llm(prompt: str, max_retries: int = 3) -> str:
    """Call the model via OpenRouter API with optimized RAG/KG prompting.
    
    Args:
        prompt: The prompt to send to the model
        max_retries: Maximum number of retry attempts for temporary failures
        
    Returns:
        The generated response from the model
    """
    retry_delay = 1  # Start with 1 second delay
    last_error = None
    
    for attempt in range(max_retries):
        try:
            if len(prompt) > MAX_PROMPT_LENGTH:
                prompt = prompt[-MAX_PROMPT_LENGTH:]
                
            logger.info(f"Sending prompt to OpenRouter (length: {len(prompt)} chars)")
            logger.debug(f"Using API URL: {API_URL}")
            logger.debug(f"Using model: {MODEL_NAME}")

            # Validate essential configuration
            if not API_URL or not API_KEY or not MODEL_NAME:
                missing = []
                if not API_KEY: missing.append("API_KEY/OPENROUTER_API_KEY")
                if not API_URL: missing.append("API_URL")
                if not MODEL_NAME: missing.append("MODEL_NAME")
                logger.error(f"Missing configuration: {', '.join(missing)}")
                return "I apologize, but the AI service is not configured correctly. Please set API_KEY, API_URL, and MODEL_NAME in the environment."
            
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://your-site.com",  # Required by OpenRouter
                "X-Title": "VilaiMathi AI"  # Your app name
            }
            
            # OpenRouter expects messages in the chat format
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "system", "content": (
                    "CRITICAL: For business queries, respond ONLY with markdown tables. NO text above tables. "
                    "NO headings above tables. NO explanatory paragraphs. Start directly with tables. "
                    "Use proper table format: headers, separator rows (|---|---|), consistent columns. "
                    "Use INR currency (₹). For quotes: first table = summary (Client Name|Project Name|Date). "
                    "Keep content minimal and professional."
                )},
                {"role": "user", "content": prompt}
            ]
            
            payload = {
                "model": MODEL_NAME,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 2000,
                "top_p": 0.9,
                "stop": ["</s>"],
                "stream": False  # Disable streaming for now
            }
        
            async with httpx.AsyncClient() as client:
                try:
                    logger.debug(f"Sending request to OpenRouter with payload: {json.dumps(payload, indent=2)}")
                    response = await client.post(
                        API_URL,
                        headers=headers,
                        json=payload,
                        timeout=120.0  # Increased timeout for larger models
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    logger.debug(f"OpenRouter response: {json.dumps(data, indent=2)}")
                    
                    if not data.get("choices"):
                        error_msg = data.get("error", {}).get("message", "No choices in response")
                        logger.error(f"OpenRouter API error: {error_msg}")
                        return f"I apologize, but the AI service returned an error: {error_msg}"
                    
                    # Extract response from OpenRouter format
                    choice = data["choices"][0]
                    if "message" in choice:
                        response_text = choice["message"]["content"]
                    elif "text" in choice:
                        response_text = choice["text"]
                    else:
                        logger.error(f"Unexpected response format from OpenRouter: {data}")
                        return "I apologize, but I received an unexpected response format from the AI service."
                    
                    logger.info(f"Received response (length: {len(response_text)} chars)")
                    
                    # Ensure we always return valid markdown and enforce table-only output
                    original_text = response_text or ""
                    response_text = enforce_tables_only(original_text)
                    if not response_text.strip():
                        # Fallback: if the model produced no tables and everything was stripped,
                        # return a default, valid table scaffold so the UI never sees empty content.
                        logger.warning("Model returned no table content; using default estimate tables fallback.")
                        response_text = generate_default_estimate_tables()
                    
                    # Ensure we always return a valid string response
                    response_text = str(response_text or "").strip()
                    if not response_text:
                        response_text = "⚠️ No response was generated. Please try again."
                        logger.warning(f"Empty response generated for query: {prompt}")
                    
                    return response_text
                    
                except httpx.ConnectTimeout:
                    last_error = "Connection to AI service timed out"
                    logger.warning(f"Attempt {attempt + 1}/{max_retries}: {last_error}")
                    if attempt == max_retries - 1:
                        return "I apologize, but I'm currently unable to connect to the AI service. Please try again later."
                        
                except httpx.HTTPStatusError as e:
                    status_code = e.response.status_code
                    if status_code == 429:  # Rate limited
                        # Respect Retry-After if present
                        retry_after = e.response.headers.get("Retry-After")
                        try:
                            retry_after = int(retry_after) if retry_after else retry_delay
                        except Exception:
                            retry_after = retry_delay
                        last_error = f"Rate limited (429). Retrying in {retry_after}s."
                        logger.warning(f"Attempt {attempt + 1}/{max_retries}: {last_error}")
                        if attempt == max_retries - 1:
                            return "Too many people are generating queries so please try again later."
                        await asyncio.sleep(retry_after)
                        retry_delay = min(retry_delay * 2, 10)
                        continue
                    elif status_code == 503:  # Service Unavailable
                        last_error = f"AI service temporarily unavailable (503)"
                        logger.warning(f"Attempt {attempt + 1}/{max_retries}: {last_error}")
                        if attempt == max_retries - 1:
                            return "I apologize, but the AI service is currently unavailable. Please try again in a few moments."
                    else:
                        logger.error(f"AI API error {status_code}: {e.response.text}")
                        return f"I apologize, but there was an error with the AI service (HTTP {status_code}). Please try again later."
                    
                except Exception as e:
                    last_error = str(e)
                    logger.error(f"Unexpected error in _call_llm (attempt {attempt + 1}): {last_error}", exc_info=True)
                    if attempt == max_retries - 1:
                        return "I apologize, but an unexpected error occurred while processing your request. Our team has been notified."
                
                # Wait before retrying with exponential backoff
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, 10)  # Cap at 10 seconds
                    logger.info(f"Retrying in {retry_delay} seconds...")
        
        except Exception as e:
            logger.error(f"Error in _call_llm: {str(e)}", exc_info=True)
            return f"I apologize, but an unexpected error occurred. Please try again later. Request: {str(e)}"

@router.post("/sessions/", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new chat session"""
    try:
        # Create new chat session
        chat_session = ChatSessionORM(
            user_id=current_user.id,
            quai_id=current_user.quai_id,
            title=session_data.title or "New Chat",
            session_metadata=session_data.metadata or {}
        )
        
        db.add(chat_session)
        await db.commit()
        await db.refresh(chat_session)
        
        return {
            "id": chat_session.session_uuid,
            "title": chat_session.title,
            "created_at": chat_session.created_at.isoformat(),
            "updated_at": chat_session.updated_at.isoformat(),
            "is_archived": chat_session.is_archived,
            "message_count": 0,
            "metadata": chat_session.session_metadata or {}
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating chat session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create chat session"
        )

@router.post("/chat", response_model=Dict[str, Any])
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Optimized chat endpoint with enhanced RAG/KG integration."""
    quote_id = str(uuid.uuid4())
    
    try:
        # Check chat limit for normal users
        if current_user.role == 'normal':
            # Count existing chat sessions for the user
            chat_count = await db.execute(
                select(func.count())
                .select_from(ChatSessionORM)
                .where(ChatSessionORM.user_id == current_user.id)
            )
            chat_count = chat_count.scalar()
            
            if chat_count >= MAX_CHATS_FOR_NORMAL_USERS:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You have reached the maximum number of chat sessions ({MAX_CHATS_FOR_NORMAL_USERS}). Please delete some chats or upgrade to premium."
                )
        
        # Get or create current chat session for the user
        chat_session_id = getattr(request, 'chat_id', None)
        
        if chat_session_id:
            # Find existing session
            session_result = await db.execute(
                select(ChatSessionORM)
                .where(
                    (ChatSessionORM.session_uuid == chat_session_id) &
                    (ChatSessionORM.user_id == current_user.id)
                )
            )
            chat_session = session_result.scalar_one_or_none()
        else:
            chat_session = None
            
        if not chat_session:
            # Create new session
            chat_session = ChatSessionORM(
                user_id=current_user.id,
                quai_id=current_user.quai_id,
                title="New Chat"
            )
            db.add(chat_session)
            await db.flush()  # Get the session ID
        
        # Get previous messages for this user and session
        history_messages = await db.execute(
            select(ChatMessageORM)
            .where(ChatMessageORM.user_id == current_user.id)
            .where(ChatMessageORM.session_id == chat_session.id)
            .order_by(ChatMessageORM.timestamp)
        )
        history_messages = history_messages.scalars().all()
        
        # Check if query is business-related
        logger.info(f"Checking if query is business-related: {request.content}")
        is_business = is_business_related(request.content)
        logger.info(f"Query business-related: {is_business}")
        
        if not is_business:
            logger.info(f"Non-business query detected, returning business-only message")
            
            # Store the non-business query and response in database
            try:
                # Store user message
                db_message = ChatMessageORM(
                    user_id=current_user.id,
                    quai_id=current_user.quai_id,
                    role=request.role,
                    content=request.content,
                    session_id=chat_session.id
                )
                db.add(db_message)
                
                # Store assistant response
                non_business_response = "**Only Business-Related Content Access**\n\nThis system is designed exclusively for business-related queries including:\n\n- Project Estimation & Services\n- Pricing & Plans\n- Business Strategy & Planning\n- Technology Recommendations\n- Industry-Specific Solutions\n\nPlease ask questions related to:\n- Project costs and timelines\n- Service quotations and pricing\n- Business strategy and planning\n- Technology recommendations for business\n- Industry-specific solutions"
                
                # Remove emojis and special characters from response
                content = non_business_response.encode('ascii', 'ignore').decode('ascii')
                assistant_message = ChatMessageORM(
                    user_id=current_user.id,
                    quai_id=current_user.quai_id,
                    role="assistant",
                    content=content,
                    session_id=chat_session.id
                )
                db.add(assistant_message)
                
                await db.commit()
                logger.info(f"Stored non-business chat messages for user {current_user.quai_id} - Chat ID: {quote_id}")
                
            except Exception as e:
                logger.error(f"Error storing non-business chat messages: {str(e)}")
                await db.rollback()
            
            return {
                "quote_id": quote_id,
                "content": non_business_response,
                "session_uuid": chat_session.session_uuid,
                "metadata": {
                    "business_related": False,
                    "error": False,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        
        # For business-related queries, enforce free user quote limit (5 per month)
        try:
            if is_business and (current_user.role or 'normal') == 'normal':
                quotes_used = int(current_user.quotes_used or 0)
                if quotes_used >= 5:
                    logger.info(f"User {current_user.id} exceeded free quote limit: {quotes_used}/5")
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail={
                            "error": "Quote limit reached",
                            "message": "You've reached your monthly limit of 5 quotes. Upgrade to Premium for unlimited quotes.",
                            "upgrade_required": True,
                            "current_plan": "normal",
                            "quotes_used": quotes_used,
                            "quotes_limit": 5
                        }
                    )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error during business limit check: {e}")
            # Continue; fallback to process normally

        try:
            # Save user message to database
            user_message = ChatMessageORM(
                user_id=current_user.id,
                quai_id=current_user.quai_id,
                role="user",
                content=request.content,
                session_id=chat_session.id
            )
            db.add(user_message)
            await db.flush()  # Ensure we get the ID
            
            # Process message with LLM
            user_query = request.content.lower()

            # Check if this is a quote/estimate request (only when user types "quotation")
            if user_query.strip() == 'quotation':
                # Get today's date in YYYY-MM-DD format
                today = datetime.now().strftime("%Y-%m-%d")
                
                # Create the response with the mandatory table
                response_content = """**MANDATORY TABLE:**

| Section         | Details         |
|-----------------|----------------|
| Client Name     | [Client's Name] |
| Project Name    | [Project Title] |
| Date            | """ + today + """ |

Please provide the following details to generate your quotation:
1. Project description
2. Required services
3. Expected timeline
4. Any specific requirements

Type your response below and I'll create a detailed quotation for you."""
                
                # Generate a unique message ID for feedback tracking
                message_id = f"msg_{int(time.time())}_{uuid.uuid4().hex[:8]}"
                
                # Save the assistant's response
                assistant_message = ChatMessageORM(
                    user_id=current_user.id,
                    quai_id=current_user.quai_id,
                    role="assistant",
                    content=response_content,
                    session_id=chat_session.id,
                    message_id=message_id  # Store the message ID in the database
                )
                db.add(assistant_message)
                
                # Increment quotes_used for normal users on business-related successful response
                if (current_user.role or 'normal') == 'normal':
                    try:
                        current_user.quotes_used = int(current_user.quotes_used or 0) + 1
                        db.add(current_user)
                    except Exception as inc_e:
                        logger.error(f"Failed to increment quotes_used: {inc_e}")

                await db.commit()
                await db.refresh(current_user)
                
                return {
                    "quote_id": quote_id,
                    "content": response_content,
                    "session_uuid": chat_session.session_uuid,
                    "message_id": message_id,  # Include message ID for feedback tracking
                    "metadata": {
                        "business_related": True,
                        "error": False,
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    "user_info": {
                        "role": current_user.role or 'normal',
                        "quotes_used": int(current_user.quotes_used or 0),
                        "quotes_limit": 5,
                        "quotes_remaining": 5 - int(current_user.quotes_used or 0) if (current_user.role or 'normal') == 'normal' else None
                    }
                }
            
            # Handle UI/UX design requests
            elif any(keyword in user_query for keyword in ['ui/ux', 'ui ux', 'design', 'wireframe', 'prototype', 'user interface', 'user experience']):
                enhanced_prompt = f"""
User Query: {request.content}

IMPORTANT: This is a UI/UX design request. Please respond with a properly formatted markdown table showing the UI/UX design services breakdown.

Business Context: {knowledge_graph.get_business_context(request.content)}
Reference Documents: {get_rag_context_sync(request.content, max_results=3)}

Please provide a detailed UI/UX design estimate with the following structure:
- Research & Discovery phase
- Wireframing phase  
- UI Design phase
- Prototyping phase
- Testing & Iteration phase

CRITICAL: Use proper markdown table format with | separators and --- separator rows.
Example:
| Service Phase | Deliverables | Estimated Cost (INR) | Timeline |
|---------------|--------------|:-------------------:|:--------:|
| Research & Discovery | User interviews, Competitor analysis | 15,000 | 1 week |

Use the exact table format specified in the system prompt.
"""
            else:
                # Specialized AI/ML cost estimation branch
                ai_ml_triggers = [
                    'ai', 'a.i.', 'machine learning', 'ml', 'data science', 'model', 'training', 'inference',
                    'llm', 'fine-tune', 'fine tune', 'dataset', 'feature engineering', 'mlops', 'deployment',
                    'computer vision', 'nlp', 'natural language', 'recommendation', 'predictive', 'classification',
                    'regression', 'forecast'
                ]
                cost_triggers = ['cost', 'estimate', 'estimation', 'pricing', 'budget', 'quotation', 'quote']
                if any(k in user_query for k in ai_ml_triggers) and any(k in user_query for k in cost_triggers):
                    enhanced_prompt = f"""
User Query: {request.content}

IMPORTANT: Provide a professional AI/ML project cost estimate using ONLY markdown tables. No headings or paragraphs. Start with the summary table.

Business Context: {knowledge_graph.get_business_context(request.content)}
Reference Documents: {get_rag_context_sync(request.content, max_results=3)}

REQUIRED TABLES AND FORMATS (use INR - ₹):

| Section | Details |
| --- | --- |
| Client Name | [Client's Name] |
| Project Name | [Project Title] |
| Date | {datetime.now().strftime('%Y-%m-%d')} |

| Scope/Assumptions | Details |
| --- | --- |
| Objective | [e.g., Build an ML model for ...] |
| Data Availability | [Existing/To be collected, size, format] |
| Quality/SLAs | [Accuracy, latency targets] |
| Compliance | [PII/PHI, GDPR, SOC2 etc.] |

| Phase | Key Tasks | Hours | Rate (₹/hr) | Subtotal (₹) | Owner |
| --- | --- | ---: | ---: | ---: | --- |
| Data Acquisition | Source integration, permissions | 24 | 2,000 | 48,000 | Data Eng |
| Data Engineering | Cleaning, feature engineering | 60 | 2,000 | 120,000 | Data Eng |
| Modeling | Baselines, experiments, tuning | 80 | 2,500 | 200,000 | ML Eng |
| Evaluation | Metrics, validation, reports | 32 | 2,500 | 80,000 | ML Eng |
| MLOps | CI/CD, model registry, versioning | 40 | 2,500 | 100,000 | MLOps |
| Deployment | API/service, scaling, security | 36 | 2,500 | 90,000 | Platform |
| Monitoring | Drift detection, alerts, dashboards | 24 | 2,000 | 48,000 | MLOps |
| PM/Meetings | Planning, reviews, communication | 24 | 2,000 | 48,000 | PM |
| Total |  | 320 |  | 734,000 |  |

| Cloud/Infra | Qty | Unit | Rate (₹) | Monthly Cost (₹) |
| --- | ---: | --- | ---: | ---: |
| GPU compute (A10) | 2 | instances | 45,000 | 90,000 |
| Storage (S3/Blob) | 500 | GB | 2 | 1,000 |
| Data transfer | 1 | TB | 5 | 5,000 |
| Total |  |  |  | 96,000 |

| One-Time Costs | Amount (₹) |
| --- | ---: |
| 3rd‑party APIs/Licenses | 50,000 |
| Security/Compliance setup | 25,000 |
| Total | 75,000 |

| Timeline | Start | End | Duration |
| --- | --- | --- | --- |
| Data & Engineering | Week 1 | Week 3 | 3 weeks |
| Modeling & Eval | Week 3 | Week 6 | 4 weeks |
| MLOps & Deploy | Week 5 | Week 7 | 3 weeks |
| UAT & Handover | Week 7 | Week 8 | 2 weeks |

| Risks/Dependencies | Impact | Mitigation |
| --- | --- | --- |
| Data quality issues | Medium | Profiling, cleansing pipelines |
| Scope creep | High | Change control, buffer 15% |
| Infra limits | Medium | Autoscaling, cost alerts |

{"Include discount/payment terms only if the user asked for a quote/quotation"}

If 'quote' or 'quotation' is detected in the user query, also include:

| Pricing | Details |
| --- | --- |
| Subtotal (Services) | [auto-sum from WBS] |
| Subtotal (Infra, 1 mo) | [from cloud table] |
| One‑Time Costs | [from one-time table] |
| Discount | [e.g., 5% for >100 hrs] |
| Grand Total | [computed] |
| Payment Terms | 50% advance, 50% on completion |

CRITICAL:
- Respond only with tables as above. No headings or prose.
- Use consistent columns with separators (| --- |) and totals rows in each table.
- Use ₹ for all amounts.
"""
                else:
                    enhanced_prompt = f"""
User Query: {request.content}

                
Business Context: {knowledge_graph.get_business_context(request.content)}
Reference Documents: {get_rag_context_sync(request.content, max_results=3)}
                
CRITICAL: Respond ONLY with markdown tables following the system's formatting rules. Do NOT include paragraphs outside tables.
- Use INR for all monetary values
- Ensure headers and separator rows exist and columns are consistent
- Include Products and Services sections when relevant
- If the user is asking for a quote, the first table MUST be the summary table (Client Name, Project Name, Date)
"""
            
            try:
                response = await _call_llm(enhanced_prompt)
                
                # Save assistant response to database
                assistant_message = ChatMessageORM(
                    user_id=current_user.id,
                    quai_id=current_user.quai_id,
                    role="assistant",
                    content=response,
                    session_id=chat_session.id  # Same session_id for conversation thread
                )
                db.add(assistant_message)
                
                # Increment quotes_used for normal users on business-related successful response
                if (current_user.role or 'normal') == 'normal':
                    try:
                        current_user.quotes_used = int(current_user.quotes_used or 0) + 1
                        db.add(current_user)
                    except Exception as inc_e:
                        logger.error(f"Failed to increment quotes_used: {inc_e}")

                await db.commit()
                await db.refresh(current_user)
                
                # Ensure we always return a valid string response
                response = str(response or "").strip()
                if not response:
                    response = "⚠️ No response was generated. Please try again."
                    logger.warning(f"Empty response generated for query: {request.content}")
                
                # Add fallback markdown formatting if empty
                response = response or "**Empty Response**\nPlease try again with more details."
                
                # Log the response
                logger.info(f"Generated response - ID: {quote_id}, Length: {len(response)}")
                
                # Standardized response format
                return {
                    "quote_id": quote_id,
                    "content": response,
                    "session_uuid": chat_session.session_uuid,  # Include session UUID for frontend
                    "metadata": {
                        "context_used": bool(knowledge_graph.get_business_context(request.content) and knowledge_graph.get_business_context(request.content) != "No relevant business context found"),
                        "documents_used": bool(get_rag_context_sync(request.content, max_results=3) and get_rag_context_sync(request.content, max_results=3) != "No relevant documents found"),
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    "user_info": {
                        "role": current_user.role or 'normal',
                        "quotes_used": int(current_user.quotes_used or 0),
                        "quotes_limit": 5,
                        "quotes_remaining": 5 - int(current_user.quotes_used or 0) if (current_user.role or 'normal') == 'normal' else None
                    }
                }
                
            except Exception as e:
                logger.error(f"Error generating LLM response: {str(e)}", exc_info=True)
                error_message = "I apologize, but I'm currently unable to connect to the AI service. This might be due to network issues or service unavailability. Please try again in a few moments."
                
                # Try to save the error message to the database
                try:
                    assistant_message = ChatMessageORM(
                        user_id=current_user.id,
                        quai_id=current_user.quai_id,
                        role="assistant",
                        content=error_message,
                        session_id=chat_session.id
                    )
                    db.add(assistant_message)
                    await db.commit()
                except Exception as db_error:
                    logger.error(f"Error saving error message to database: {str(db_error)}")
                    await db.rollback()
                
                return {
                    "quote_id": quote_id,
                    "content": error_message,
                    "session_uuid": chat_session.session_uuid,
                    "metadata": {
                        "error": True,
                        "error_message": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
        
        except Exception as e:
            await db.rollback()
            logger.error(f"Database error: {str(e)}", exc_info=True)
            # Continue with response even if db fails
            error_message = "I apologize, but there was an issue saving your conversation."
            return {
                "quote_id": str(uuid.uuid4()),
                "content": error_message,
                "session_uuid": getattr(chat_session, 'session_uuid', str(uuid.uuid4())),
                "metadata": {
                    "error": True,
                    "error_message": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        error_message = "REACHED YOUR QUOTES LIMIT."
        return {
            "quote_id": str(uuid.uuid4()),
            "content": error_message,
            "session_uuid": getattr(chat_session, 'session_uuid', str(uuid.uuid4())),
            "metadata": {
                "error": True,
                "error_message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        }

@router.post("/estimate/uiux", response_model=QuoteResponse)
async def uiux_estimate(project_details: Dict[str, Any]):
    """Generate structured UI/UX estimate with professional formatting."""
    try:
        # Get current date and set quote validity
        current_date = datetime.now().strftime("%d %b %Y")
        valid_until = (datetime.now() + timedelta(days=30)).strftime("%d %b %Y")
        quote_number = f"UI-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
        
        # Get project details with defaults
        client_name = project_details.get('client_name', '[Client\'s Name]')
        project_name = project_details.get('project_name', '[Project Title]')
        
        # Format the project details into a professional quote
        quote_content = f"""
## UI/UX Design Quote

### Summary
- Client: {client_name}
- Project: {project_name}
- Date: {current_date}
- Quote #: {quote_number}

### Itemized Estimate
| Item | Qty/Hours | Rate (₹) | Subtotal (₹) |
|---|---:|---:|---:|
| Research & Discovery | 40 | 2,000 | 80,000 |
| Wireframing | 30 | 2,000 | 60,000 |
| UI Design | 50 | 2,000 | 100,000 |
| Prototyping | 30 | 2,000 | 60,000 |
| Testing & Iteration | 30 | 2,000 | 60,000 |
| | | **Subtotal** | **360,000** |

### Discounts
- Standard 5% discount for projects over 100 hours: (₹18,000)

### Totals
- Subtotal: ₹360,000
- Discount: (₹18,000)
- Grand Total: ₹342,000

### Timeline and Payment Terms
- Timeline: 01 Sep 2025 – 30 Sep 2025 (4 weeks)
- Quote Valid Until: {valid_until}
- Payment Terms: 50% advance, 50% on completion
- Hourly Rate: ₹2,000/hour

### Next Steps
1. Review and approve this quotation
2. Sign the NDA and service agreement
3. Schedule project kickoff meeting
4. Submit 50% advance payment to begin work
"""

        # Return the formatted quote
        return QuoteResponse(
            client_name=client_name,
            project_name=project_name,
            date=current_date,
            scope_of_work={
                'Research & Discovery': ['User interviews', 'Competitive analysis', 'User personas'],
                'Wireframing': ['Low-fidelity wireframes for all screens'],
                'UI Design': ['High-fidelity mockups', 'Visual style guide'],
                'Prototyping': ['Interactive clickable prototype'],
                'Testing & Iteration': ['Usability testing', 'Revisions', 'Final polish']
            },
            timeline="01 Sep 2025 – 30 Sep 2025 (4 weeks)",
            pricing={
                'Research & Discovery': 80000,
                'Wireframing': 60000,
                'UI Design': 100000,
                'Prototyping': 60000,
                'Testing & Iteration': 60000
            },
            total=342000,
            notes=f"Quote valid until {valid_until}",
            payment_terms="50% advance, 50% on completion"
        )
    except Exception as e:
        logger.error(f"Error generating UI/UX estimate: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate UI/UX estimate"
        )

@router.get("/sessions/", response_model=List[ChatSessionResponse])
async def list_chat_sessions(
    archived: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all chat sessions for the current user"""
    try:
        result = await db.execute(
            select(ChatSessionORM)
            .where(
                (ChatSessionORM.user_id == current_user.id) &
                (ChatSessionORM.is_archived == archived)
            )
            .order_by(ChatSessionORM.updated_at.desc())
            .options(selectinload(ChatSessionORM.messages))
        )
        
        sessions = result.scalars().all()
        return [
            {
                "id": session.session_uuid,
                "title": session.title,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "is_archived": session.is_archived,
                "message_count": len(session.messages),
                "metadata": session.session_metadata or {}
            }
            for session in sessions
        ]
    except Exception as e:
        logger.error(f"Error listing chat sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list chat sessions"
        )

@router.get("/sessions/{session_uuid}", response_model=Dict[str, Any])
async def get_chat_session(
    session_uuid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get details of a specific chat session"""
    try:
        result = await db.execute(
            select(ChatSessionORM)
            .where(
                (ChatSessionORM.session_uuid == session_uuid) &
                (ChatSessionORM.user_id == current_user.id)
            )
            .options(
                selectinload(ChatSessionORM.messages),
                selectinload(ChatSessionORM.documents)
            )
        )
        
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or access denied"
            )
            
        return {
            "id": session.session_uuid,
            "title": session.title,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "is_archived": session.is_archived,
            "message_count": len(session.messages),
            "metadata": session.session_metadata or {},
            "documents": [doc.to_dict() for doc in session.documents]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching chat session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch chat session"
        )

@router.patch("/sessions/{session_uuid}", response_model=ChatSessionResponse)
async def update_chat_session(
    session_uuid: str,
    update_data: ChatSessionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a chat session"""
    try:
        # Get the session to update
        result = await db.execute(
            select(ChatSessionORM)
            .where(
                (ChatSessionORM.session_uuid == session_uuid) &
                (ChatSessionORM.user_id == current_user.id)
            )
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or access denied"
            )
        
        # Update fields if provided
        update_values = {}
        if update_data.title is not None:
            update_values["title"] = update_data.title
        if update_data.is_archived is not None:
            update_values["is_archived"] = update_data.is_archived
        if update_data.metadata is not None:
            update_values["session_metadata"] = {**session.session_metadata, **update_data.metadata}
        
        if update_values:
            update_values["updated_at"] = datetime.utcnow()
            await db.execute(
                update(ChatSessionORM)
                .where(ChatSessionORM.id == session.id)
                .values(**update_values)
            )
            await db.commit()
            
            # Refresh the session to get updated values
            await db.refresh(session)
        
        return {
            "id": session.session_uuid,
            "title": session.title,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "is_archived": session.is_archived,
            "message_count": len(session.messages),
            "metadata": session.session_metadata or {}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating chat session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update chat session"
        )

@router.delete("/sessions/{session_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    session_uuid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a chat session and all its messages"""
    try:
        # Get the session to delete
        result = await db.execute(
            select(ChatSessionORM)
            .where(
                (ChatSessionORM.session_uuid == session_uuid) &
                (ChatSessionORM.user_id == current_user.id)
            )
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or access denied"
            )
        
        # Delete the session (cascade will handle messages and documents)
        await db.execute(
            delete(ChatSessionORM)
            .where(ChatSessionORM.id == session.id)
        )
        await db.commit()
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting chat session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete chat session"
        )

@router.get("/sessions/{session_uuid}/messages", response_model=List[ChatMessageResponse])
async def get_session_messages(
    session_uuid: str,
    limit: int = None,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get messages for a specific chat session.
    
    Premium users have no message limit, while free users are limited to CHAT_HISTORY_LIMIT.
    """
    # Check if user is premium and no specific limit is provided
    if limit is None:
        if current_user.role == 'premium':
            # No limit for premium users
            limit = None
        else:
            # Apply default limit for free users
            limit = CHAT_HISTORY_LIMIT
        
    try:
        # Verify session belongs to user
        session_result = await db.execute(
            select(ChatSessionORM)
            .where(
                (ChatSessionORM.session_uuid == session_uuid) &
                (ChatSessionORM.user_id == current_user.id)
            )
        )
        session = session_result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or access denied"
            )
        
        # Build the base query
        query = (
            select(ChatMessageORM)
            .where(ChatMessageORM.session_id == session.id)
            .order_by(ChatMessageORM.timestamp.asc())
            .offset(offset)
        )
        
        # Only apply limit for non-premium users or when explicitly set
        if limit is not None:
            query = query.limit(limit)
            
        # Execute the query
        messages_result = await db.execute(query)
        
        messages = messages_result.scalars().all()
        return [
            {
                "id": msg.message_uuid,
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "metadata": msg.meta or {}
            }
            for msg in messages
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching session messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch session messages"
        )

@router.post("/sessions/{session_uuid}/messages", response_model=ChatMessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    session_uuid: str,
    message: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new message in a chat session"""
    try:
        # Verify session belongs to user
        session_result = await db.execute(
            select(ChatSessionORM)
            .where(
                (ChatSessionORM.session_uuid == session_uuid) &
                (ChatSessionORM.user_id == current_user.id)
            )
        )
        session = session_result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or access denied"
            )
        
        # Create the message
        db_message = ChatMessageORM(
            user_id=current_user.id,
            quai_id=current_user.quai_id,
            session_id=session.id,
            role=message.role,
            content=message.content,
            metadata=message.metadata or {}
        )
        
        db.add(db_message)
        
        # Update session's updated_at timestamp
        session.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(db_message)
        
        return {
            "id": db_message.message_uuid,
            "role": db_message.role,
            "content": db_message.content,
            "timestamp": db_message.timestamp.isoformat(),
            "metadata": db_message.metadata or {}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create message"
        )

class BusinessChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    is_premium: bool = Field(default=False, description="Whether this is a premium user request")

# Now initialize RL Optimizer after SYSTEM_PROMPT is defined
try:
    from app.rl_optimizer import QuoteGenerator, QuoteInteractionTracker
    rl_optimizer = QuoteGenerator(SYSTEM_PROMPT)
    interaction_tracker = QuoteInteractionTracker()
    logger.info("RL Optimizer initialized successfully")
except ImportError as e:
    logger.warning(f"Could not initialize RL Optimizer: {e}")
    rl_optimizer = None
    interaction_tracker = None

# In-memory store for chat sessions (in production, use Redis or database)
chat_sessions = {}

# Business chat endpoint with continuous conversation support
@router.post("/business-chat", response_model=Dict[str, Any])
async def business_chat(
    request: BusinessChatRequest,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Business-focused chat endpoint with continuous conversation support.
    Maintains chat history using session ID and only processes business-related queries.
    """
    try:
        # Get or create session
        session_id = request.session_id or x_session_id or str(uuid.uuid4())
        
        # Initialize session if it doesn't exist
        if session_id not in chat_sessions:
            chat_sessions[session_id] = {
                'history': [],
                'created_at': datetime.utcnow().isoformat(),
                'last_activity': datetime.utcnow().isoformat()
            }
        
        session = chat_sessions[session_id]
        session['last_activity'] = datetime.utcnow().isoformat()
        
        # Check if query is business-related
        if not is_business_related(request.message):
            return {
                "content": "I'm designed to assist with business-related queries. "
                          "Please ask me about business, project estimation, or related topics.",
                "is_business_related": False,
                "session_id": session_id,
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "query_type": "non_business"
                }
            }
        
        # Add user message to history
        user_message = {"role": "user", "content": request.message}
        session['history'].append(user_message)
        
        # Prepare chat request with history
        chat_request = ChatRequest(
            role="user",
            content=request.message,
            chat_id=session_id,
            history=session['history'][-10:]  # Keep last 10 messages for context
        )
        
        # Process business query using the main chat function
        response = await chat(chat_request, db, current_user)
        
        # Add assistant response to history
        if isinstance(response, dict) and 'content' in response:
            assistant_message = {"role": "assistant", "content": response['content']}
            session['history'].append(assistant_message)
            
            # Clean up old sessions (optional, for memory management)
            cleanup_inactive_sessions()
            
            return {
                "content": response['content'],
                "is_business_related": True,
                "session_id": session_id,
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "history_length": len(session['history'])
                }
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unexpected response format from chat service"
            )
        
    except Exception as e:
        logger.error(f"Error in business chat: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your request"
        )

def cleanup_inactive_sessions(max_inactive_minutes: int = 60, max_sessions: int = 1000):
    """Clean up inactive chat sessions to manage memory usage"""
    global chat_sessions
    
    # If we have too many sessions, remove the oldest ones first
    if len(chat_sessions) > max_sessions:
        # Sort sessions by last activity and keep only the most recent ones
        sorted_sessions = sorted(
            chat_sessions.items(),
            key=lambda x: x[1]['last_activity'],
            reverse=True
        )
        chat_sessions = dict(sorted_sessions[:max_sessions])
    
    # Remove sessions that have been inactive for too long
    now = datetime.utcnow()
    inactive_session_ids = [
        session_id for session_id, session in chat_sessions.items()
        if (now - datetime.fromisoformat(session['last_activity'])).total_seconds() > max_inactive_minutes * 60
    ]
    
    for session_id in inactive_session_ids:
        del chat_sessions[session_id]
    
    if inactive_session_ids:
        logger.info(f"Cleaned up {len(inactive_session_ids)} inactive chat sessions")

# Initialize the quote generator if not already done
if 'quote_generator' not in globals():
    from app.rl_optimizer import QuoteGenerator
    quote_generator = QuoteGenerator(base_prompt=SYSTEM_PROMPT)

@router.post("/track_interaction")
async def track_interaction(
    interaction: QuoteInteraction, 
    db: AsyncSession = Depends(get_db)
):
    """
    Track how users interact with generated quotes.
    
    Args:
        interaction: The interaction details
        db: Database session
    """
    try:
        logger.info(f"Tracking interaction: {interaction}")
        
        # Create a new interaction record
        interaction_data = interaction.dict()
        interaction_data['metadata'] = json.dumps(interaction_data.get('metadata', {}))
        
        # Convert features_used to a JSON string if it exists
        if 'features_used' in interaction_data and interaction_data['features_used'] is not None:
            interaction_data['features_used'] = json.dumps(interaction_data['features_used'])
        
        # Check edit limit for non-premium users
        if interaction.interaction_type == 'edit':
            user = await db.get(User, interaction.user_id)
            if user and user.role != 'premium':
                # Count previous edits by this user
                edit_count = await db.execute(
                    select(func.count(QuoteInteractionORM.id)).where(
                        (QuoteInteractionORM.user_id == interaction.user_id) &
                        (QuoteInteractionORM.interaction_type == 'edit')
                    )
                )
                edit_count = edit_count.scalar() or 0
                
                if edit_count >= 5:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Free users are limited to 5 quote edits. Upgrade to premium for unlimited edits."
                    )
        
        # Create the interaction record
        interaction_orm = QuoteInteractionORM(**interaction_data)
        db.add(interaction_orm)
        
        # If this is a quote generation, update the user's quote count
        if interaction.interaction_type == 'generate':
            user = await db.get(User, interaction_data.get('user_id'))
            if user and user.role != 'premium':
                user.quotes_used = (user.quotes_used or 0) + 1
                db.add(user)
        
        await db.commit()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking interaction: {e}", exc_info=True)
        # Don't raise the exception to avoid failing the main operation
        await db.rollback()
        return {"status": "error", "message": str(e)}

# Chat session management endpoints
@router.get("/sessions/")
async def get_chat_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all chat sessions for the current user."""
    try:
        result = await db.execute(
            select(ChatSessionORM)
            .filter(ChatSessionORM.user_id == current_user.id)
            .order_by(ChatSessionORM.updated_at.desc())
        )
        sessions = result.scalars().all()
        return [
            {
                "id": str(session.id),
                "title": session.title,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "message_count": session.message_count or 0,
                "is_archived": session.is_archived or False,
                "metadata": session.metadata or {}
            }
            for session in sessions
        ]
    except Exception as e:
        logger.error(f"Error fetching chat sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch chat sessions"
        )

# Premium features configuration
PREMIUM_FEATURES = {
    'unlimited_quotes': True,
    'watermark_free': True,
    'high_quality_pdf': True,
    'custom_branding': True,
    'priority_support': True
}

# Premium feature flags with descriptions for the frontend
PREMIUM_FEATURE_DESCRIPTIONS = {
    'unlimited_quotes': 'Generate unlimited professional quotations',
    'watermark_free': 'Export documents without watermarks',
    'high_quality_pdf': 'High-quality PDF exports with professional formatting',
    'custom_branding': 'Add your company logo and branding to documents',
    'priority_support': 'Priority email and chat support'
}

# In-memory cache for recent estimates (replace with Redis in production)
RECENT_ESTIMATES = []
MAX_RECENT_ESTIMATES = 10

@router.get("/estimates/recent")
async def get_recent_estimates(limit: int = 5):
    """Get recent estimates from the cache."""
    return RECENT_ESTIMATES[-limit:]

def check_quote_limit(user: User) -> bool:
    """Check if user has reached their quote limit."""
    if user.role == 'premium':
        return False  # Premium users have no limit
    return (user.quotes_used or 0) >= MAX_QUOTES_FOR_NORMAL_USERS

@router.post("/quotes/generate", response_model=QuoteResponse)
async def generate_quote(
    quote_request: Union[QuoteRequestModel, PremiumQuotationRequest],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a professional quotation with detailed breakdown.
    
    For premium users, includes additional features like custom branding and watermark-free exports.
    """
    try:
        # Check if user has reached their quote limit
        if check_quote_limit(current_user):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=(
                    f"You've reached your monthly limit of {MAX_QUOTES_FOR_NORMAL_USERS} quotes. "
                    "Upgrade to Premium for unlimited quotes and premium features."
                )
            )
        
        # Convert to dict for processing
        quote_data = quote_request.dict()
        
        # Check if this is a premium request
        is_premium = current_user.role == 'premium' or isinstance(quote_request, PremiumQuotationRequest)
        
        # Generate the quotation
        quotation_generator = PremiumQuotationGenerator()
        
        # For premium users, use premium features
        if is_premium and isinstance(quote_request, PremiumQuotationRequest):
            # Handle premium-specific features
            include_watermark = quote_data.get('include_watermark', False)
            custom_logo = quote_data.get('custom_logo_url')
            custom_terms = quote_data.get('custom_terms', [])
            
            # Add custom terms if provided
            if custom_terms and isinstance(custom_terms, list):
                if 'terms' not in quote_data:
                    quote_data['terms'] = []
                quote_data['terms'].extend(custom_terms)
            
            # Generate the quotation with premium features
            quotation = quotation_generator.generate_quotation(quote_data, {
                'id': current_user.id,
                'email': current_user.email,
                'name': current_user.username
            })
            
            # Track this interaction
            interaction = QuoteInteraction(
                quote_id=quotation['quotation_id'],
                interaction_type='generate',
                user_role='premium',
                features_used=['premium_quotation', 'custom_terms'] + 
                            (['custom_branding'] if custom_logo else []) +
                            (['watermark_free'] if not include_watermark else [])
            )
        else:
            # Standard quotation for non-premium users
            quotation = quotation_generator.generate_quotation(quote_data, {
                'id': current_user.id,
                'email': current_user.email,
                'name': current_user.username
            })
            
            # Track this interaction
            interaction = QuoteInteraction(
                quote_id=quotation['quotation_id'],
                interaction_type='generate',
                user_role='normal'
            )
        
        # Save the interaction
        await track_interaction(interaction, db)
        
        # For non-premium users, increment quote count
        if current_user.role != 'premium':
            current_user.quotes_used = (current_user.quotes_used or 0) + 1
            db.add(current_user)
            await db.commit()
        
        return quotation
        
    except Exception as e:
        logger.error(f"Error generating quote: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate quotation. Please try again."
        )

@router.get("/quotes/{quote_id}/export/pdf")
async def export_quote_pdf(
    quote_id: str,
    include_watermark: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Export a quote as a PDF document.
    
    Premium users can export without watermarks and with custom branding.
    """
    try:
        # In a real app, you would fetch the quote from the database
        # For now, we'll just generate a sample quote
        quote_data = {
            'quotation_id': quote_id,
            'date_created': datetime.now().strftime("%Y-%m-%d"),
            'client': {
                'name': 'Sample Client',
                'email': 'client@example.com',
                'company': 'Client Company'
            },
            'project': {
                'name': 'Sample Project',
                'description': 'This is a sample project description',
                'timeline': '4 weeks'
            },
            'line_items': [
                {
                    'description': 'Sample Service',
                    'quantity': '10',
                    'unit': 'hours',
                    'unit_price': '1,000.00',
                    'total': '10,000.00'
                }
            ],
            'summary': {
                'subtotal': '10,000.00',
                'tax_rate': '18%',
                'tax_amount': '1,800.00',
                'discount': '0.00',
                'total': '11,800.00',
                'currency': 'INR'
            },
            'terms': [
                '50% advance payment required',
                'Balance payment on completion',
                'Prices valid for 30 days'
            ],
            'notes': 'Thank you for your business!'
        }
        
        # Check if user can export without watermark
        can_export_without_watermark = current_user.role == 'premium' and not include_watermark
        
        # Generate PDF
        quotation_generator = PremiumQuotationGenerator()
        pdf_path = quotation_generator.export_to_pdf(
            quote_data,
            include_watermark=not can_export_without_watermark
        )
        
        # Track this interaction
        interaction = QuoteInteraction(
            quote_id=quote_id,
            interaction_type='export_pdf',
            user_role=current_user.role,
            features_used=['export_pdf'] + 
                        (['watermark_free'] if not include_watermark and current_user.role == 'premium' else [])
        )
        await track_interaction(interaction, db)
        
        # Return the PDF file
        return FileResponse(
            pdf_path,
            media_type='application/pdf',
            filename=f"quotation_{quote_id}.pdf"
        )
        
    except Exception as e:
        logger.error(f"Error exporting quote to PDF: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export quotation to PDF. Please try again."
        )

@router.get("/features/premium")
async def get_premium_features():
    """Get information about premium features and their descriptions."""
    return {
        'features': PREMIUM_FEATURES,
        'descriptions': PREMIUM_FEATURE_DESCRIPTIONS
    }

from fastapi import UploadFile, File, HTTPException, status
from pathlib import Path
import shutil
from typing import List

@router.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Handle multiple file uploads"""
    UPLOAD_DIR = Path("uploads")
    UPLOAD_DIR.mkdir(exist_ok=True)
    
    saved_files = []
    for file in files:
        # Validate file type
        if file.filename.split('.')[-1].lower() not in ['pdf', 'doc', 'docx']:
            continue
            
        # Save file
        file_path = UPLOAD_DIR / f"{uuid.uuid4()}_{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create DB record
        doc = DocumentORM(
            user_id=current_user.id,
            filename=file.filename,
            filepath=str(file_path),
            filetype=file.content_type,
            filesize=file_path.stat().st_size
        )
        db.add(doc)
        await db.commit()
        saved_files.append(doc)
    
    return {"message": f"Successfully uploaded {len(saved_files)} files", "files": saved_files}

@router.get("/documents", response_model=List[dict])
async def get_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all documents for current user"""
    result = await db.execute(
        select(DocumentORM)
        .where(DocumentORM.user_id == current_user.id)
        .order_by(DocumentORM.uploaded_at.desc())
    )
    return [{
        "id": doc.id,
        "filename": doc.filename,
        "filetype": doc.filetype,
        "uploaded_at": doc.uploaded_at,
        "session_id": doc.session_id
    } for doc in result.scalars().all()]