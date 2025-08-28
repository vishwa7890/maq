"""
Base model and database configuration.
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import os
from pathlib import Path

# Database configuration
import logging
from sqlalchemy.exc import SQLAlchemyError
from tenacity import retry, stop_after_attempt, wait_exponential
import urllib.parse

logger = logging.getLogger(__name__)

def get_database_url() -> str:
    """Get database URL from environment with proper formatting."""
    # First try to get the direct DATABASE_URL
    db_url = os.getenv("DATABASE_URL")
    
    if db_url:
        # Handle Render's PostgreSQL connection string format
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql+asyncpg://', 1)
        return db_url
    
    # Fall back to individual components
    db_user = os.getenv("POSTGRES_USER")
    db_password = os.getenv("POSTGRES_PASSWORD")
    db_host = os.getenv("POSTGRES_HOST")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB")
    
    if all([db_user, db_password, db_host, db_name]):
        # URL encode the password to handle special characters
        safe_password = urllib.parse.quote_plus(db_password)
        return f"postgresql+asyncpg://{db_user}:{safe_password}@{db_host}:{db_port}/{db_name}"
    
    raise ValueError(
        "Database configuration is incomplete. "
        "Set either DATABASE_URL or all POSTGRES_* environment variables"
    )

# Get the database URL
DATABASE_URL = get_database_url()
logger.info(f"Using database: {DATABASE_URL.split('@')[-1]}")

# Create SQLAlchemy engine and session factory with connection pooling
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Set to False in production for better performance
    future=True,
    pool_pre_ping=True,  # Enable connection health checks
    pool_size=5,        # Size of the connection pool
    max_overflow=10,    # Max connections that can be created beyond pool_size
    pool_timeout=30,    # Seconds to wait before giving up on getting a connection
    pool_recycle=300,   # Recycle connections after 5 minutes
    connect_args={
        'command_timeout': 10,  # Timeout for connection attempts
        'server_settings': {
            'application_name': 'quotemaster_api',
            'timezone': 'UTC'
        }
    }
)

async_session_maker = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True
)
async def get_db() -> AsyncSession:
    """Dependency that provides a database session with retry logic.
    
    Yields:
        AsyncSession: An async database session
    """
    async with async_session_maker() as session:
        try:
            # Test the connection
            await session.execute("SELECT 1")
            yield session
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Database error: {str(e)}")
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Unexpected error: {str(e)}")
            raise
        finally:
            await session.close()

# Create base class for all models
Base = declarative_base()

# For synchronous operations (Alembic, testing, etc.)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine.sync_engine if hasattr(engine, 'sync_engine') else None
)

# Dependency to get DB session
async def get_db() -> AsyncSession:
    """Dependency that provides a database session.
    
    Yields:
        AsyncSession: An async database session
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
