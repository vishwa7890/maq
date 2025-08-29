"""
Base model and database configuration.
"""
import logging
import os
import urllib.parse
from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

logger = logging.getLogger(__name__)

def get_database_url() -> str:
    """Get database URL from environment with proper formatting for asyncpg."""
    # First try to get the direct DATABASE_URL
    db_url = os.getenv("DATABASE_URL")
    
    logger.info(f"Initial DATABASE_URL: {db_url}")
    
    if not db_url:
        logger.info("DATABASE_URL not found, checking individual components...")
        # Fall back to individual components if DATABASE_URL is not set
        db_user = os.getenv("POSTGRES_USER")
        db_password = os.getenv("POSTGRES_PASSWORD")
        db_host = os.getenv("POSTGRES_HOST")
        db_port = os.getenv("POSTGRES_PORT", "5432")
        db_name = os.getenv("POSTGRES_DB")
        
        logger.info(f"DB Components - User: {db_user}, Host: {db_host}, Port: {db_port}, DB: {db_name}")
        
        if all([db_user, db_password, db_host, db_name]):
            # URL encode the password to handle special characters
            safe_password = urllib.parse.quote_plus(db_password)
            db_url = f"postgresql+asyncpg://{db_user}:{'*' * 8}@{db_host}:{db_port}/{db_name}"
            logger.info(f"Constructed DB URL: {db_url}")
        else:
            error_msg = "Database configuration is incomplete. "
            error_msg += "Set either DATABASE_URL or all POSTGRES_* environment variables"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    # Ensure we're using the correct asyncpg URL format
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
        logger.info(f"Updated DB URL to async format: {db_url}")
    
    logger.info(f"Final database URL: {db_url.split('@')[-1] if '@' in db_url else db_url}")
    return db_url

# Get the database URL
DATABASE_URL = get_database_url()
logger.info(f"Using database: {DATABASE_URL.split('@')[-1]}")

# Create async engine with explicit asyncpg dialect
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
        'server_settings': {
            'application_name': 'quotemaster_api',
            'timezone': 'UTC'
        }
    }
)

# Create async session factory
async_session_maker = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Base class for models
Base = declarative_base()

# Dependency to get DB session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides a database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database error: {str(e)}")
            raise
        finally:
            await session.close()

# Connection pool settings are now in the engine configuration above

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
