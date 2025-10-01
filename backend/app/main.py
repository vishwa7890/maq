import os
import logging
import sys
import signal
import json
import jwt
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Request, status, Response, Depends, HTTPException, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.exceptions import RequestValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

from .chat_router import router as chat_router
from .pdf_router import router as file_router
from app.api.endpoints.feedback import router as feedback_router
from models.base import get_db
from models import User, Base
from .schemas import UserCreate, UserLogin, UserOut
from app.auth import (
    hash_password, 
    verify_password, 
    create_access_token, 
    get_user_by_username, 
    get_user_by_email,
    get_current_user
)

# Removed SentenceTransformer import - now using Hugging Face API

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
# Set to 100 years (effectively never expires)
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 365 * 100

def configure_logging():
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
                'stream': 'ext://sys.stdout'
            },
        },
        'loggers': {
            'sqlalchemy.engine': {
                'level': 'WARNING',  
                'handlers': ['console'],
                'propagate': False
            },
            '': {
                'level': 'INFO',
                'handlers': ['console']
            }
        }
    })

# Configure logging
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="VilaiMathi AI",
    version="1.0.0",
    description="AI-powered business quotation assistant with RAG and knowledge graph",
    docs_url="/docs",
    redoc_url=None
)

# CORS configuration
# Read comma-separated origins from env, e.g. "https://luminaquo.mindapt.in,https://example.com"
cors_origins_env = os.getenv("CORS_ORIGINS", "")
allow_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]

# If no CORS_ORIGINS set, use FRONTEND_URL as fallback
if not allow_origins:
    frontend_url = os.getenv("FRONTEND_URL", "")
    if frontend_url:
        allow_origins.append(frontend_url)
    # Add common development and production URLs
    allow_origins.extend([
        "http://localhost:3000", 
        "http://localhost:3001",
        "https://luminaquo.mindapt.in"
    ])

# Remove any empty strings and ensure unique origins
allow_origins = list(set(filter(None, allow_origins)))

# Log CORS configuration for debugging
logger.info(f"CORS_ORIGINS env: '{cors_origins_env}'")
logger.info(f"FRONTEND_URL env: '{os.getenv('FRONTEND_URL', 'not set')}'")
logger.info(f"Final allow_origins: {allow_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Lightweight auth router for debugging routing from Vercel/Netlify
auth_router = APIRouter()

@auth_router.get("/ping")
async def auth_ping(request: Request):
    return {"user": "test-user"}

@auth_router.get("/me-debug")
async def auth_me_debug():
    """Debug endpoint that returns a mock user without auth."""
    return {"user": "test-user"}

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(file_router, prefix="/api/files", tags=["files"])
app.include_router(feedback_router, prefix="/api/feedback", tags=["feedback"])

# Initialize database tables on startup
@app.on_event("startup")
async def startup_db():
    """Initialize database tables on startup."""
    from models.base import engine
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

# Use the get_db dependency from models.base

@app.post("/auth/register", response_model=dict)
async def register(
    response: Response,
    user: UserCreate, 
    db: AsyncSession = Depends(get_db)
):
    """Register a new user and automatically log them in."""
    # Check if username already exists
    if await get_user_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="Username already registered")
        
    # Check if email already exists
    if await get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
        
    # Validate email domain
    allowed_domains = ["gmail.com", "yahoo.com"]  # Add your allowed domains here
    email_domain = user.email.split('@')[-1].lower()
    if email_domain not in allowed_domains:
        raise HTTPException(
            status_code=400, 
            detail=f"Only emails from the following domains are allowed: {', '.join(allowed_domains)}"
        )
    
    # Determine role from payload; default to 'normal' and validate
    role = getattr(user, 'role', 'normal') or 'normal'
    role = role.lower()
    if role not in {"normal", "premium"}:
        role = "normal"

    # Create the user
    db_user = User(
        username=user.username,
        email=user.email,
        phone_number=user.phone_number,
        hashed_password=hash_password(user.password),
        role=role,
    )
    db.add(db_user)
    
    try:
        await db.commit()
        await db.refresh(db_user)
        
        # Create access token for the new user (without expiration)
        access_token = create_access_token({"sub": db_user.username, "user_id": db_user.id}, expires_delta=None)
        
        # Set the access token as an HTTP-only cookie
        # For cross-site requests (frontend on 3000, backend on 8000), use SameSite=None and path="/".
        # In production over HTTPS, set secure=True.
        # No max_age since the token doesn't expire
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            samesite="none",  # Use None for cross-site cookies in production
            secure=True,  # True in production with HTTPS
            path="/",
        )
        
        # Return success response with redirect URL
        return {
            "message": "Registration successful", 
            "redirect": "/chat",
            "user": {
                "id": db_user.id,
                "username": db_user.username,
                "email": db_user.email,
                "role": getattr(db_user, 'role', 'normal')
            }
        }
        
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="User already exists")

@app.post("/auth/login", response_model=dict)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"Login attempt for username: {form_data.username}")
    
    # Try direct query approach
    try:
        from sqlalchemy.future import select
        result = await db.execute(select(User).where(User.username == form_data.username))
        user = result.scalars().first()
        logger.info(f"Direct query result - User found: {user is not None}")
        
        if user:
            logger.info(f"User details: id={user.id}, username={user.username}, role={getattr(user, 'role', 'unknown')}")
        
    except Exception as e:
        logger.error(f"Direct query failed: {e}")
        user = None
    
    if not user:
        logger.warning(f"User not found: {form_data.username}")
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    password_valid = verify_password(form_data.password, user.hashed_password)
    logger.info(f"Password verification result: {password_valid}")
    
    if not password_valid:
        logger.warning(f"Invalid password for user: {form_data.username}")
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    # Create access token (without expiration)
    access_token = create_access_token({"sub": user.username, "user_id": user.id}, expires_delta=None)
    
    # Set the access token as an HTTP-only cookie
    # For cross-site requests (frontend on 3000, backend on 8000), use SameSite=None and path="/".
    # In production over HTTPS, set secure=True.
    # No max_age since the token doesn't expire
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="none",  # Use None for cross-site cookies in production
        secure=True,  # True in production with HTTPS
        path="/",
    )
    
    # Return success response with redirect URL
    frontend_url = os.getenv("FRONTEND_URL")
    return {"message": "Login successful", "redirect": f"{frontend_url}/chat"}

@app.post("/auth/logout")
async def logout(response: Response):
    """Logout user by clearing the authentication cookie."""
    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="none",
        secure=True,  # Match cookie attributes to ensure deletion in production
        path="/",
    )
    frontend_url = os.getenv("FRONTEND_URL")
    return {"message": "Successfully logged out", "redirect": f"{frontend_url}/auth"}


@app.get("/auth/me", response_model=dict)
async def me(current_user: User = Depends(get_current_user)):
    """Return the current authenticated user's info."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {
        "id": getattr(current_user, 'id', None),
        "username": getattr(current_user, 'username', None),
        "email": getattr(current_user, 'email', None),
        "role": getattr(current_user, 'role', 'normal'),
        "quotes_used": getattr(current_user, 'quotes_used', 0),
    }


@app.get("/debug/cors")
async def debug_cors():
    cors_origins_env = os.getenv("CORS_ORIGINS", "")
    allow_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]
    
    if not allow_origins:
        frontend_url = os.getenv("FRONTEND_URL", "")
        if frontend_url:
            allow_origins.append(frontend_url)
        allow_origins.extend(["http://localhost:3000", "http://localhost:3001"])
    
    return {
        "CORS_ORIGINS_env": cors_origins_env,
        "FRONTEND_URL_env": os.getenv("FRONTEND_URL"),
        "allow_origins": allow_origins,
    }


@app.post("/auth/upgrade", response_model=dict)
async def upgrade_to_premium(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upgrade the current user to premium."""
    logger.info(f"Upgrade request for user: {current_user.username}, current role: {getattr(current_user, 'role', 'normal')}")
    
    if getattr(current_user, 'role', 'normal') == 'premium':
        return {"message": "Already premium", "role": "premium"}
    
    # Direct assignment to trigger SQLAlchemy dirty tracking
    current_user.role = 'premium'
    
    try:
        await db.commit()
        await db.refresh(current_user)
        logger.info(f"Successfully upgraded user {current_user.username} to premium. New role: {current_user.role}")
        return {"message": "Upgraded to premium", "role": current_user.role}
    except Exception as e:
        logger.error(f"Failed to upgrade user {current_user.username}: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to upgrade user")


@app.post("/auth/role/{role}", response_model=dict)
async def set_role(
    role: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Set the current user's role explicitly to 'normal' or 'premium'."""
    role = role.lower()
    if role not in {"normal", "premium"}:
        raise HTTPException(status_code=400, detail="Invalid role. Use 'normal' or 'premium'.")
    
    logger.info(f"Setting role for user {current_user.username} from {getattr(current_user, 'role', 'normal')} to {role}")
    
    # Direct assignment to trigger SQLAlchemy dirty tracking
    current_user.role = role
    
    try:
        await db.commit()
        await db.refresh(current_user)
        logger.info(f"Successfully set role for user {current_user.username} to {current_user.role}")
        return {"message": "Role updated", "role": current_user.role}
    except Exception as e:
        logger.error(f"Failed to set role for user {current_user.username}: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update role")


@app.post("/api/quotes/generate", response_model=dict)
async def generate_quote(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate a quote with plan limitations enforced."""
    try:
        body = await request.json()
        prompt = body.get("prompt", "")
        
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        # Check quote limits for normal users
        user_role = current_user.role or 'normal'
        quotes_used = current_user.quotes_used or 0
        
        if user_role == 'normal' and quotes_used >= 5:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Quote limit reached",
                    "message": "You've reached your monthly limit of 5 quotes. Upgrade to Premium for unlimited quotes.",
                    "upgrade_required": True,
                    "current_plan": "normal",
                    "quotes_used": quotes_used,
                    "quotes_limit": 5
                }
            )
        
        # Generate the quote (mock implementation)
        quote_data = {
            "id": f"quote_{quotes_used + 1}",
            "title": f"Quote for: {prompt[:50]}...",
            "items": [
                {"description": "Initial consultation", "quantity": 1, "rate": 150, "amount": 150},
                {"description": "Project development", "quantity": 20, "rate": 100, "amount": 2000},
                {"description": "Testing and deployment", "quantity": 5, "rate": 120, "amount": 600}
            ],
            "subtotal": 2750,
            "tax": 275,
            "total": 3025,
            "terms": "Payment due within 30 days",
            "has_watermark": user_role == 'normal',
            "can_edit": user_role == 'premium',
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Increment quotes_used for normal users
        if user_role == 'normal':
            try:
                current_user.quotes_used = (current_user.quotes_used or 0) + 1
                db.add(current_user)
                await db.commit()
                await db.refresh(current_user)
            except Exception as e:
                logger.error(f"Failed to update quotes_used: {str(e)}")
                await db.rollback()
                raise HTTPException(status_code=500, detail="Failed to update quote usage")
        
        return {
            "success": True,
            "message": "Quote generated successfully",
            "quote": quote_data,
            "user_info": {
                "role": user_role,
                "quotes_used": current_user.quotes_used or 0,
                "quotes_remaining": 5 - getattr(current_user, 'quotes_used', 0) if user_role == 'normal' else "unlimited"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating quote: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate quote")


@app.on_event("startup")
async def startup_event():
    """Handle application startup."""
    # Configure logging first
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting up application...")
        
        # Application now uses Hugging Face API instead of local models
        logger.info("Application configured to use Hugging Face API for embeddings")
        
        # Add any startup tasks here
        
        # Log successful startup
        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Error during startup: {e}", exc_info=True)
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Handle application shutdown."""
    logger = logging.getLogger(__name__)
    logger.info("Shutting down application...")
    try:
        # Add any cleanup tasks here
        # Close any database connections, file handles, etc.
        logger.info("Cleanup complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)
    finally:
        # Ensure all logs are flushed
        logging.shutdown()
        print("\nApplication shutdown complete.")

# Create static directory if it doesn't exist
static_dir = Path(__file__).parent.parent / 'static'
static_dir.mkdir(exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Also mount app static files
app_static_dir = Path(__file__).parent / 'static'
if app_static_dir.exists():
    app.mount("/app/static", StaticFiles(directory=app_static_dir), name="app_static")

# Add favicon route
@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    favicon_path = static_dir / 'favicon.ico'
    if not favicon_path.exists():
        # Return a transparent 1x1 pixel if favicon.ico doesn't exist
        return Response(status_code=204)
    return FileResponse(favicon_path)

# (Removed duplicate CORS middleware that allowed wildcard origins with credentials)

# (Removed duplicate router includes that prefixed with "/api")

@app.get("/")
async def root(request: Request):
    """
    Root endpoint that checks authentication and redirects accordingly.
    """
    # Check for access token in cookies
    access_token = request.cookies.get("access_token")
    
    if not access_token:
        # No token found, redirect to frontend auth page
        frontend_url = os.getenv("FRONTEND_URL")
        return RedirectResponse(url=f"{frontend_url}/auth")
    
    # Token exists, verify it
    try:
        # Remove 'Bearer ' prefix if present
        if access_token.startswith("Bearer "):
            access_token = access_token[7:]
            
        # Verify the token
        payload = jwt.decode(
            access_token, 
            SECRET_KEY, 
            algorithms=[ALGORITHM]
        )
        
        # Token is valid, redirect to frontend chat
        frontend_url = os.getenv("FRONTEND_URL")
        return RedirectResponse(url=f"{frontend_url}/chat")
        
    except jwt.PyJWTError:
        # Invalid token, clear cookie and redirect to frontend auth
        frontend_url = os.getenv("FRONTEND_URL")
        response = RedirectResponse(url=f"{frontend_url}/auth")
        response.delete_cookie("access_token")
        return response



@app.get("/api")
async def api_info() -> dict:
    """API information endpoint."""
    return {
        "message": "Welcome to AI QuoteMaster API",
        "docs": "/docs",
        "endpoints": {
            "chat": "/chat",
            "quotes": "/quote/",
            "health": "/ping"
        }
    }


@app.get("/ping")
async def ping() -> dict:
    """Health-check endpoint."""
    return {
        "status": "ok",
        "service": "QuoteMaster API",
        "version": "0.1.0"
    }

@app.get("/cors-debug")
async def cors_debug():
    cors_origins_env = os.getenv("CORS_ORIGINS", "")
    allow_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]
    
    if not allow_origins:
        frontend_url = os.getenv("FRONTEND_URL", "")
        if frontend_url:
            allow_origins.append(frontend_url)
        allow_origins.extend(["http://localhost:3000", "http://localhost:3001"])
    
    return {
        "cors_origins_env": cors_origins_env,
        "frontend_url": os.getenv("FRONTEND_URL", "not set"),
        "allow_origins": allow_origins
    }

# Dashboard and Profile Routes

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request, current_user: User = Depends(get_current_user)):
    """Serve the dashboard page with user data."""
    try:
        # Get the absolute path to the dashboard template
        templates_dir = Path(__file__).parent / "templates"
        dashboard_path = templates_dir / "dashboard.html"
        
        # Debug: Log the path being checked
        logger.info(f"Looking for dashboard template at: {dashboard_path}")
        logger.info(f"Template exists: {dashboard_path.exists()}")
        
        # Ensure the template exists
        if not dashboard_path.exists():
            # Try an alternative path for development
            alt_path = Path.cwd() / "app" / "templates" / "dashboard.html"
            if alt_path.exists():
                dashboard_path = alt_path
                logger.info(f"Using alternative template path: {dashboard_path}")
            else:
                # Log the directory contents for debugging
                try:
                    contents = list(templates_dir.glob('*'))
                    logger.error(f"Template directory contents: {contents}")
                except Exception as e:
                    logger.error(f"Error reading template directory: {e}")
                
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Dashboard template not found at: {dashboard_path} or {alt_path}"
                )
            
        # Read the template
        with open(dashboard_path, 'r', encoding='utf-8') as f:
            template = f.read()
            
        # Prepare user data
        dashboard_data = {
            "username": getattr(current_user, 'username', 'User'),
            "email": getattr(current_user, 'email', ''),
            "join_date": getattr(current_user, 'created_at', datetime.utcnow()).strftime("%B %d, %Y"),
            "last_login": datetime.utcnow().strftime("%B %d, %Y %H:%M"),
            "is_admin": getattr(current_user, 'is_admin', False)
        }
        
        # Add user data as a JavaScript variable for frontend use
        user_script = f"""
        <script>
            window.userData = {json.dumps(dashboard_data, default=str)};
        </script>
        """
        
        # Insert the user script before the closing head tag
        if "</head>" in template:
            template = template.replace("</head>", f"{user_script}\n</head>")
        else:
            # If no head tag, add it at the end of the head section
            template = template.replace("<body>", f"{user_script}\n<body>")
        
        # Replace placeholders with actual user data
        template = template.replace("Loading...", dashboard_data["username"])
            
        return HTMLResponse(content=template, status_code=200)
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading dashboard: {str(e)}"
        )

@app.get("/profile", response_class=HTMLResponse)
async def profile_page(current_user: User = Depends(get_current_user)):
    """Serve the user profile page."""
    try:
        # In a real app, you would render a profile template with the user's data
        # For now, we'll redirect to the chat page with a success message
        response = RedirectResponse(url="/chat", status_code=status.HTTP_302_FOUND)
        response.set_cookie(
            key="profile_message",
            value="Profile page is under construction!",
            max_age=5,  # Message will be shown for 5 seconds
            httponly=True,
            samesite="lax"
        )
        return response
    except Exception as e:
        logger.error(f"Error loading profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error loading profile"
        )

# Exception handlers
@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"message": f"The requested URL {request.url} was not found"},
    )

@app.exception_handler(500)
async def server_error_exception_handler(request: Request, exc: Exception):
    logger.error(f"Server error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error occurred"},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )

if __name__ == "__main__":
    import uvicorn
    
    try:
        logger.info("Starting Business Knowledge Chat server...")
        logger.info("Server will be available at: http://localhost:8008")
        logger.info("Press Ctrl+C to stop the server")
        
        # Run uvicorn directly without multiprocessing
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=False,  # Disable reload to avoid multiprocessing issues
            access_log=True
        )
        
    except KeyboardInterrupt:
        logger.info("\nServer stopped by user")
        print("\nGoodbye!")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
