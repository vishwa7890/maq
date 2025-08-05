"""
Database management and utilities for the application.
Handles database connections, schema management, and provides utility functions.
"""
import asyncio
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
import json
import logging
from dotenv import load_dotenv

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Load environment variables
load_dotenv(Path(__file__).parent.parent / '.env')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration from environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/questimate")

# Create SQLAlchemy engine and session factory
engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()

# Import models to ensure they're registered with SQLAlchemy
from app.models import User, Quote, ChatMessageORM, QuoteInteractionORM

class DatabaseManager:
    """Main database management class with all database operations."""
    
    @staticmethod
    async def test_connection() -> bool:
        """Test the database connection."""
        try:
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
                logger.info("✅ Database connection successful")
                return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False

    @staticmethod
    async def create_tables() -> bool:
        """Create all database tables."""
        logger.info("Creating database tables...")
        try:
            async with engine.begin() as conn:
                # Create UUID extension if it doesn't exist
                await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
                # Create all tables
                await conn.run_sync(Base.metadata.create_all)
                logger.info("✅ All tables created successfully")
                return True
        except Exception as e:
            logger.error(f"❌ Error creating tables: {e}")
            return False

    @staticmethod
    async def drop_tables() -> bool:
        """Drop all database tables."""
        logger.info("Dropping all tables...")
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
                logger.info("✅ All tables dropped successfully")
                return True
        except Exception as e:
            logger.error(f"❌ Error dropping tables: {e}")
            return False

    @staticmethod
    async def reset_database() -> bool:
        """Reset the entire database (drop and recreate all tables)."""
        if await DatabaseManager.drop_tables():
            return await DatabaseManager.create_tables()
        return False

    @staticmethod
    async def get_table_info() -> Dict[str, Any]:
        """Get information about all tables in the database."""
        result = {"tables": [], "record_counts": {}}
        
        try:
            async with engine.begin() as conn:
                # Get all tables
                tables_result = await conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name;
                
                
                
                """))
                tables = [row[0] for row in tables_result.fetchall()]
                result["tables"] = tables
                
                # Get record counts for each table
                for table in tables:
                    count_result = await conn.execute(
                        text(f'SELECT COUNT(*) FROM "{table}"')
                    )
                    result["record_counts"][table] = count_result.scalar()
                
                return result
                
        except Exception as e:
            logger.error(f"Error getting table info: {e}")
            return {"error": str(e)}

    @classmethod
    async def get_session(cls) -> AsyncSession:
        """Get a new database session."""
        return async_session_maker()

    @classmethod
    async def execute_query(cls, query: str, params: Optional[Dict] = None) -> List[Tuple]:
        """Execute a raw SQL query and return results."""
        async with async_session_maker() as session:
            try:
                result = await session.execute(text(query), params or {})
                await session.commit()
                return result.fetchall()
            except Exception as e:
                await session.rollback()
                logger.error(f"Error executing query: {e}")
                raise


# Command-line interface
async def main():
    """Handle command-line database operations."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database management utility")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Test connection command
    subparsers.add_parser("test", help="Test database connection")
    
    # Create tables command
    subparsers.add_parser("create", help="Create all database tables")
    
    # Drop tables command
    subparsers.add_parser("drop", help="Drop all database tables")
    
    # Reset database command
    subparsers.add_parser("reset", help="Reset database (drop and recreate all tables)")
    
    # Show info command
    subparsers.add_parser("info", help="Show database information")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == "test":
            if await DatabaseManager.test_connection():
                print("✅ Database connection successful")
            else:
                print("❌ Database connection failed")
                
        elif args.command == "create":
            if await DatabaseManager.create_tables():
                print("✅ Tables created successfully")
            else:
                print("❌ Failed to create tables")
                
        elif args.command == "drop":
            confirm = input("⚠️  Are you sure you want to drop all tables? (yes/no): ")
            if confirm.lower() == 'yes':
                if await DatabaseManager.drop_tables():
                    print("✅ Tables dropped successfully")
                else:
                    print("❌ Failed to drop tables")
            else:
                print("Operation cancelled")
                
        elif args.command == "reset":
            confirm = input("⚠️  Are you sure you want to reset the database? (yes/no): ")
            if confirm.lower() == 'yes':
                if await DatabaseManager.reset_database():
                    print("✅ Database reset successfully")
                else:
                    print("❌ Failed to reset database")
            else:
                print("Operation cancelled")
                
        elif args.command == "info":
            info = await DatabaseManager.get_table_info()
            if "error" in info:
                print(f"❌ Error: {info['error']}")
            else:
                print("\n📊 Database Information")
                print("=" * 40)
                print("\n📋 Tables:")
                for table in info["tables"]:
                    count = info["record_counts"].get(table, 0)
                    print(f"  - {table}: {count} records")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
