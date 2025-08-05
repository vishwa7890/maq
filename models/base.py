"""
Base model and database configuration.
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import os
from pathlib import Path

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:123@localhost:5432/quotemaster"
)

# Create SQLAlchemy engine and session factory
engine = create_async_engine(DATABASE_URL, echo=True, future=True)
async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

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
