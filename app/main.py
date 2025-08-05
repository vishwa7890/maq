import os
import logging
import sys
import signal
import json
import jwt
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Request, status, Response, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse, RedirectResponse
from fastapi.exceptions import RequestValidationError
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

from .chat_router import router as chat_router
from .pdf_router import router as file_router
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

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

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
    title="QuestiMate",
    version="1.0.0",
    description="Chat interface with RAG and knowledge graph for business insights",
    docs_url="/docs",
    redoc_url=None
)

# Include routers
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(file_router, prefix="/api/files", tags=["files"])

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8008", "http://127.0.0.1:8008"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    
    # Create the user
    db_user = User(
        username=user.username,
        email=user.email,
        phone_number=user.phone_number,
        hashed_password=hash_password(user.password)
    )
    db.add(db_user)
    
    try:
        await db.commit()
        await db.refresh(db_user)
        
        # Create access token for the new user
        access_token = create_access_token({"sub": db_user.username, "user_id": db_user.id})
        
        # Set the access token as an HTTP-only cookie
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            max_age=3600,  # 1 hour
            samesite="lax",
            secure=False,  # Set to True in production with HTTPS
        )
        
        # Return success response with redirect URL
        return {
            "message": "Registration successful", 
            "redirect": "/chat",
            "user": {
                "id": db_user.id,
                "username": db_user.username,
                "email": db_user.email
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
    user = await get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    # Create access token
    access_token = create_access_token({"sub": user.username, "user_id": user.id})
    
    # Set the access token as an HTTP-only cookie
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=3600,  # 1 hour
        samesite="lax",
        secure=False,  # Set to True in production with HTTPS
    )
    
    # Return success response with redirect URL
    return {"message": "Login successful", "redirect": "/chat"}

@app.post("/auth/logout")
async def logout(response: Response):
    """Logout user by clearing the authentication cookie."""
    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax",
        secure=False,  # Set to True in production with HTTPS
    )
    return {"message": "Successfully logged out", "redirect": "/login"}


@app.on_event("startup")
async def startup_event():
    """Handle application startup."""
    # Configure logging first
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting up application...")
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

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600  # Cache preflight requests for 10 minutes
)

# Include routers
app.include_router(chat_router, prefix="/api")
app.include_router(file_router, prefix="/api")

@app.get("/")
async def root(request: Request):
    """
    Root endpoint that checks authentication and redirects accordingly.
    """
    # Check for access token in cookies
    access_token = request.cookies.get("access_token")
    
    if not access_token:
        # No token found, redirect to login
        return RedirectResponse(url="/login")
    
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
        
        # Token is valid, redirect to chat
        return RedirectResponse(url="/chat")
        
    except jwt.PyJWTError:
        # Invalid token, clear cookie and redirect to login
        response = RedirectResponse(url="/login")
        response.delete_cookie("access_token")
        return response

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """Serve the login page."""
    try:
        # Use absolute path to the login.html file
        login_path = Path(__file__).parent / 'templates' / 'login.html'
        if not login_path.exists():
            raise FileNotFoundError(f"Login template not found at {login_path}")
        return FileResponse(login_path)
    except FileNotFoundError as e:
        logger.error(f"Login page not found: {e}")
        return HTMLResponse("Login page not found", status_code=404)

@app.get("/chat", response_class=HTMLResponse)
async def chat_page(current_user: User = Depends(get_current_user)):
    """Serve the main chat interface with authentication check."""
    try:
        # Check if user is authenticated
        if not current_user:
            return RedirectResponse(url="/login")
            
        # Get the path to the index.html file
        index_path = Path(__file__).parent / "templates" / "index.html"
        logger.info(f"Looking for template at: {index_path}")
        
        # Check if the file exists
        if not index_path.exists():
            logger.error(f"Template file not found at {index_path}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Template file not found"
            )
            
        # Read the HTML file
        with open(index_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Inject the API URL
        api_url = os.getenv("API_URL", "http://localhost:8000")
        html_content = html_content.replace("{{API_URL}}", api_url)
        
        # Add username as a meta tag if not already present
        if '<meta name="username"' not in html_content:
            username_meta = f'<meta name="username" content="{current_user.username}">'
            html_content = html_content.replace('</head>', f'    {username_meta}\n</head>')
        
        # Update the username display
        if 'id="usernameDisplay">' in html_content:
            display_name = current_user.username.split('@')[0] if '@' in current_user.username else current_user.username
            html_content = html_content.replace(
                'id="usernameDisplay">User<',
                f'id="usernameDisplay">{display_name}<'
            )
        
        return HTMLResponse(content=html_content, status_code=200)
    except Exception as e:
        logger.error(f"Error serving chat page: {e}")
        return HTMLResponse("An error occurred while loading the chat interface", status_code=500)


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
            port=8008,
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
