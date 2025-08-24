import os
import logging
import json
import hashlib
import time
import uuid
import shutil
from functools import lru_cache
from pathlib import Path
import asyncio
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import httpx
from fastapi import (
    APIRouter, Depends, HTTPException, Request, 
    BackgroundTasks, status, UploadFile, File, Body
)
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

# Initialize logger
logger = logging.getLogger(__name__)

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
    QuoteRequest as QuoteRequestModel
)
from app.knowledge_graph import BusinessKnowledgeGraph, Entity
from app.rag_engine import get_rag_context
from models.base import get_db
from app.auth import get_current_user

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
    SYSTEM_PROMPT = """You are Lumina Quo AI, an expert in business quotes and estimates. Your goal is to provide accurate, relevant, and actionable business advice with properly formatted tables.

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
    """Check if the query is business-related."""
    import re
    query_lower = query.lower()
    
    # Business-related keywords and phrases
    business_keywords = [
        # Project Estimation & Services
        'cost', 'price', 'estimate', 'quotation', 'quote', 'budget', 'timeline', 'deadline',
        'ui/ux', 'ui ux', 'design', 'development', 'software', 'app', 'website', 'web',
        'mobile', 'frontend', 'backend', 'full-stack', 'prototype', 'wireframe',
        'service', 'package', 'project', 'deliverable', 'milestone',
        
        # Pricing & Plans
        'pricing', 'plan', 'package', 'gst', 'tax', 'payment', 'discount', 'startup',
        'enterprise', 'premium', 'basic', 'plan', 'subscription', 'billing',
        
        # Business Strategy & Planning
        'strategy', 'planning', 'business', 'industry', 'market', 'competitive',
        'analysis', 'recommendation', 'tech stack', 'technology', 'scalable',
        'mvp', 'saas', 'platform', 'optimization', 'branding', 'research',
        
        # Technology & Development
        'development', 'programming', 'coding', 'technology', 'tech', 'stack',
        'framework', 'database', 'api', 'integration', 'deployment',
        
        # Industry & Domain
        'industry', 'sector', 'domain', 'vertical', 'market', 'business model',
        'revenue', 'profit', 'investment', 'roi', 'growth', 'scale',
        'capital investment', 'business capital', 'venture capital',
        
        # Common business terms
        'client', 'customer', 'vendor', 'supplier', 'partner', 'stakeholder',
        'requirement', 'specification', 'scope', 'deliverable', 'quality',
        'maintenance', 'support', 'consulting', 'advisory', 'expertise'

        # discount
        'discount',
    ]
    
    # Check if any business keyword is present
    for keyword in business_keywords:
        if keyword in query_lower:
            return True
    
    # Check for specific business question patterns
    business_patterns = [
        r'how much.*cost',
        r'what.*price',
        r'estimate.*project',
        r'quote.*service',
        r'timeline.*project',
        r'pricing.*plan',
        r'business.*strategy',
        r'tech.*stack',
        r'development.*cost',
        r'design.*service',
        r'consulting.*fee',
        r'project.*budget',
        r'service.*package',
        r'payment.*terms',
        r'industry.*recommendation'
    ]
    
    # Check for non-business patterns (should return False)
    non_business_patterns = [
        r'weather',
        r'joke',
        r'cook',
        r'capital.*france',
        r'homework',
        r'meaning.*life',
        r'hobby',
        r'movie',
        r'guitar',
        r'recipe',
        r'book',
        r'population',
        r'car',
        r'exercise'
    ]
    
    # If any non-business pattern matches, return False
    for pattern in non_business_patterns:
        if re.search(pattern, query_lower):
            return False
    
    for pattern in business_patterns:
        if re.search(pattern, query_lower):
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
                "X-Title": "Lumina Quo AI"  # Your app name
            }
            
            # OpenRouter expects messages in the chat format
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "system", "content": (
                    "CRITICAL: Respond ONLY using properly formatted markdown tables as per the system rules. "
                    "Do NOT include paragraphs outside tables. Ensure headers, separator rows, consistent column counts, "
                    "and INR currency where monetary values are shown. If the user asks for a quotation, the first table MUST be the summary table."
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
                    
                    # Ensure we always return valid markdown
                    response_text = response_text or "No content generated"
                    if not response_text.startswith('#') and not response_text.startswith('**'):
                        response_text = f"**Response**:\n{response_text}"
                    
                    # Fix table formatting if needed
                    response_text = fix_table_formatting(response_text)
                    
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
                            return "I apologize, but the AI service is receiving too many requests right now. Please try again shortly."
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
| **Client Name** | [Client's Name] |
| **Project Name**| [Project Title] |
| **Date**        | """ + today + """ |

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
                await db.commit()
                
                return {
                    "quote_id": quote_id,
                    "content": response_content,
                    "session_uuid": chat_session.session_uuid,
                    "message_id": message_id,  # Include message ID for feedback tracking
                    "metadata": {
                        "business_related": True,
                        "error": False,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
            
            # Handle UI/UX design requests
            elif any(keyword in user_query for keyword in ['ui/ux', 'ui ux', 'design', 'wireframe', 'prototype', 'user interface', 'user experience']):
                enhanced_prompt = f"""
User Query: {request.content}

IMPORTANT: This is a UI/UX design request. Please respond with a properly formatted markdown table showing the UI/UX design services breakdown.

Business Context: {knowledge_graph.get_business_context(request.content)}
Reference Documents: {get_rag_context(request.content, max_results=3)}

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
                enhanced_prompt = f"""
User Query: {request.content}

                
Business Context: {knowledge_graph.get_business_context(request.content)}
Reference Documents: {get_rag_context(request.content, max_results=3)}
                
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
                await db.commit()
                
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
                        "documents_used": bool(get_rag_context(request.content, max_results=3) and get_rag_context(request.content, max_results=3) != "No relevant documents found"),
                        "timestamp": datetime.utcnow().isoformat()
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
        error_message = "I apologize, but an unexpected error occurred while processing your request."
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
    """Generate structured UI/UX estimate."""
    try:
        # Format the project details into a prompt
        prompt = f"""
        Generate a detailed UI/UX estimate with this structure:
        
        Client Name: {project_details.get('client_name', "[Client's Name]")}
        Project Name: {project_details.get('project_name', "[Project Title]")}
        
        Scope of Work:
        - User Research (Persona creation, surveys, interviews)
        - Competitive Analysis
        - Information Architecture (Sitemap & User Flows)
        - Wireframes (Low-fidelity + High-fidelity)
        - Interactive Prototypes (Figma/InVision)
        - Visual Design (Color palette, typography, UI components)
        - Design Handoff (Style guide & assets for developers)
        
        Timeline: 3 to 4 Weeks
        
        Pricing in INR:
        - Research & Discovery: 10000
        - Wireframes: 7500
        - UI Design: 15000
        - Prototyping & Revisions: 5000
        - Design Handoff: 2500
        
        Notes: This is a fixed-price quote. Additional revisions or scope changes may incur extra costs.
        
        Return ONLY valid JSON matching this schema:
        {{'client_name': str, 'project_name': str, 'scope_of_work': {{'Phase': ['Activity1', 'Activity2']}}, 'timeline': str, 'pricing': {{'Item': float}}, 'total': float, 'notes': str, 'payment_terms': str}}
        """
        
        response_text = await _call_llm(prompt)
        
        try:
            quote_data = json.loads(response_text)
            # Calculate total if not provided
            if "total" not in quote_data:
                quote_data["total"] = sum(quote_data["pricing"].values())
            return QuoteResponse(**quote_data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse quote response: {response_text}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse quote response: {str(e)}")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating chat session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create chat session"
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
    """Get messages for a specific chat session"""
    # Use CHAT_HISTORY_LIMIT if no specific limit is provided
    if limit is None:
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
        
        # Get messages for this session
        messages_result = await db.execute(
            select(ChatMessageORM)
            .where(ChatMessageORM.session_id == session.id)
            .order_by(ChatMessageORM.timestamp.asc())
            .limit(limit)
            .offset(offset)
        )
        
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

# Now initialize RL Optimizer after SYSTEM_PROMPT is defined
try:
    from app.rl_optimizer import QuoteGenerator, QuoteInteractionTracker
    rl_optimizer = QuoteGenerator(SYSTEM_PROMPT)
    logger.info("RL Optimizer initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize RL Optimizer: {e}")
    rl_optimizer = None
    SYSTEM_PROMPT = """You are Lumina Quo AI, an expert in business quotes and estimates. Your goal is to provide accurate, relevant, and actionable business advice with properly formatted tables.
    
**MANDATORY TABLE : only for quotation requests otherwise ignore**

| Section         | Details         |
|-----------------|----------------|
| **Client Name** | [Client's Name] |
| **Project Type** | [Type of Project] |
| **Estimated Hours** | [Number] |
| **Rate** | [Rate per hour] |
| **Total Estimate** | [Calculated Total] |
| **Timeline** | [Estimated Timeline] |
| **Next Steps** | [Recommended Actions] |"""

# Initialize the quote generator if not already done
if 'quote_generator' not in globals():
    from app.rl_optimizer import QuoteGenerator
    quote_generator = QuoteGenerator(base_prompt=SYSTEM_PROMPT)

@router.post("/track_interaction")
async def track_interaction(interaction: QuoteInteraction):
    """Track how users interact with generated quotes."""
    try:
        quote_generator.track_quote_interaction(
            quote_id=interaction.quote_id,
            interaction_type=interaction.interaction_type,
            metadata=interaction.metadata or {}
        )
        return {"status": "success", "message": "Interaction tracked successfully"}
    except Exception as e:
        logger.error(f"Error tracking interaction: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}

# Chat session management endpoints
@router.get("/sessions/")
async def get_chat_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all chat sessions for the current user"""
    try:
        result = await db.execute(
            select(ChatSessionORM)
            .where(ChatSessionORM.user_id == current_user.id)
            .order_by(ChatSessionORM.updated_at.desc())
        )
        sessions = result.scalars().all()
        
        session_list = []
        for session in sessions:
            # Count messages in this session
            message_count_result = await db.execute(
                select(ChatMessageORM)
                .where(ChatMessageORM.session_id == session.id)
            )
            message_count = len(message_count_result.scalars().all())
            
            session_list.append({
                "id": session.id,
                "session_uuid": session.session_uuid,
                "title": session.title,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "message_count": message_count
            })
        
        return session_list
    except Exception as e:
        logger.error(f"Error fetching chat sessions: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch chat sessions")

@router.post("/sessions/")
async def create_chat_session(
    session_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new chat session"""
    try:
        new_session = ChatSessionORM(
            user_id=current_user.id,
            quai_id=current_user.quai_id,
            title=session_data.get('title', 'New Chat')
        )
        db.add(new_session)
        await db.commit()
        await db.refresh(new_session)
        
        return {
            "id": new_session.id,
            "session_uuid": new_session.session_uuid,
            "title": new_session.title,
            "created_at": new_session.created_at.isoformat(),
            "updated_at": new_session.updated_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Error creating chat session: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create chat session")

@router.patch("/sessions/{session_uuid}")
async def update_chat_session(
    session_uuid: str,
    update_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a chat session"""
    try:
        # Log the incoming request data for debugging
        logger.info(f"Updating chat session {session_uuid} with data: {update_data}")
        
        # Start a transaction
        async with db.begin():
            # Get the chat session with proper locking to prevent concurrent updates
            result = await db.execute(
                select(ChatSessionORM)
                .where(ChatSessionORM.session_uuid == session_uuid)
                .where(ChatSessionORM.user_id == current_user.id)
                .with_for_update()
            )
            session = result.scalar_one_or_none()
            
            if not session:
                logger.warning(f"Chat session {session_uuid} not found for user {current_user.id}")
                raise HTTPException(status_code=404, detail="Chat session not found")
            
            # Update fields from the request
            if 'title' in update_data and update_data['title']:
                session.title = update_data['title']
                session.updated_at = datetime.utcnow()
                logger.info(f"Updated session {session_uuid} title to: {session.title}")
            
            # Commit the transaction
            await db.commit()
        
        # Refresh the session to get updated values
        await db.refresh(session)
        
        # Return the updated session data
        return {
            "id": session.id,
            "session_uuid": session.session_uuid,
            "title": session.title,
            "updated_at": session.updated_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating chat session: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update chat session")

@router.delete("/sessions/{session_uuid}")
async def delete_chat_session(
    session_uuid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a chat session and all its related messages and documents"""
    try:
        # Start a transaction
        async with db.begin():
            # Get the session with all relationships loaded
            stmt = (
                select(ChatSessionORM)
                .options(
                    selectinload(ChatSessionORM.messages),
                    selectinload(ChatSessionORM.documents)
                )
                .where(ChatSessionORM.session_uuid == session_uuid)
                .where(ChatSessionORM.user_id == current_user.id)
            )
            result = await db.execute(stmt)
            session = result.scalar_one_or_none()
            
            if not session:
                raise HTTPException(status_code=404, detail="Chat session not found")
            
            # Explicitly delete all messages first
            for message in session.messages:
                await db.delete(message)
            
            # Explicitly delete all documents
            for document in session.documents:
                await db.delete(document)
            
            # Flush to ensure all deletes are processed
            await db.flush()
            
            # Now delete the session
            await db.delete(session)
            
        return {"message": "Chat session and all related data deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat session: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete chat session: {str(e)}"
        )

@router.get("/sessions/{session_uuid}/messages")
async def get_session_messages(
    session_uuid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all messages for a specific chat session"""
    try:
        # Verify session belongs to user
        session_result = await db.execute(
            select(ChatSessionORM)
            .where(ChatSessionORM.session_uuid == session_uuid)
            .where(ChatSessionORM.user_id == current_user.id)
        )
        session = session_result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        # Get messages
        result = await db.execute(
            select(ChatMessageORM)
            .where(ChatMessageORM.session_id == session.id)
            .order_by(ChatMessageORM.timestamp)
        )
        messages = result.scalars().all()
        
        return [{
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat()
        } for msg in messages]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching session messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch session messages")

# Analytics endpoints
@router.get("/analytics/stats")
async def get_analytics_stats():
    """Get summary statistics for the dashboard."""
    try:
        # In a real implementation, this would query your database
        # For now, we'll return mock data
        return {
            "totalQuotes": len(quote_generator.quote_history) if quote_generator else 0,
            "avgEngagement": 0.65,  
            "topPromptScore": 0.82,  
            "topPromptDesc": quote_generator.get_best_prompt()[:100] + "..." if quote_generator else "N/A"
        }
    except Exception as e:
        logger.error(f"Error getting analytics stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/interactions")
async def get_interaction_analytics():
    """Get interaction data for the dashboard."""
    try:
        # In a real implementation, this would query your database
        # For now, we'll return mock data
        return {
            "timeSeries": {
                "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                "values": [12, 19, 3, 5, 2, 3, 15]
            },
            "byType": {
                "labels": ["View", "Download", "Copy", "Edit", "Share"],
                "values": [300, 150, 80, 40, 30]
            },
            "recent": [
                {
                    "quote_id": "abc123xyz",
                    "timestamp": "2023-06-15T14:30:00Z",
                    "interaction_type": "download",
                    "metadata": {"source": "button"}
                },
                {
                    "quote_id": "def456uvw",
                    "timestamp": "2023-06-15T14:25:00Z",
                    "interaction_type": "copy",
                    "metadata": {"text_length": 42}
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error getting interaction analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Feedback model
class FeedbackRequest(BaseModel):
    message_id: str
    feedback: str  # 'positive' or 'negative'
    session_id: Optional[str] = None
    user_query: Optional[str] = None
    assistant_response: Optional[str] = None

# Feedback endpoint
@router.post("/feedback")
async def submit_feedback(
    feedback: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Handle user feedback on assistant responses for reinforcement learning.
    """
    try:
        if not rl_optimizer:
            logger.warning("RL Optimizer not available")
            return {"status": "error", "message": "RL Optimizer not available"}

        # Log the feedback
        logger.info(
            f"Feedback received - Message ID: {feedback.message_id}, "
            f"Type: {feedback.feedback}, "
            f"Session: {feedback.session_id}"
        )

        # Track the interaction in RL optimizer
        interaction_type = "download" if feedback.feedback == "positive" else "ignore"
        
        # Store additional metadata
        metadata = {
            "user_id": str(current_user.id) if current_user else "anonymous",
            "session_id": feedback.session_id,
            "user_query": feedback.user_query,
            "assistant_response": feedback.assistant_response
        }
        
        # Track the interaction
        rl_optimizer.track_quote_interaction(
            quote_id=feedback.message_id,
            interaction_type=interaction_type,
            metadata=metadata
        )

        # Update the database with feedback (optional)
        try:
            # Find the message in the database and update its feedback
            result = await db.execute(
                select(ChatMessageORM)
                .where(ChatMessageORM.message_id == feedback.message_id)
            )
            message = result.scalars().first()
            
            if message:
                # Update feedback in the database
                message.feedback = feedback.feedback
                message.updated_at = datetime.utcnow()
                await db.commit()
        except Exception as db_error:
            logger.error(f"Error updating feedback in database: {db_error}")
            # Don't fail the request if DB update fails

        return {"status": "success", "message": "Feedback received"}
        
    except Exception as e:
        logger.error(f"Error processing feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process feedback"
        )

# Chat configuration
CHAT_HISTORY_LIMIT = int(os.getenv("CHAT_HISTORY_LIMIT", "20"))

# In-memory cache for recent estimates
RECENT_ESTIMATES = []
MAX_RECENT_ESTIMATES = int(os.getenv("MAX_RECENT_ESTIMATES", "10"))

@router.get("/estimates/recent")
async def get_recent_estimates(limit: int = 5):
    """Get recent estimates from the cache."""
    return {"estimates": RECENT_ESTIMATES[-limit:]}

from fastapi import UploadFile, File, Body, HTTPException, status
from pathlib import Path
import shutil
from pydantic import BaseModel
from typing import Optional, Dict, Any, List, Union
from app.rl_optimizer import QuoteGenerator, QuoteInteractionTracker

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