#!/usr/bin/env python3
"""
Script to reset a user's password in the database.
Usage: python reset_password.py <username> <new_password>
"""
import asyncio
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.base import async_session_maker
from models.user import User
from app.auth import hash_password

async def reset_user_password(username: str, new_password: str):
    """Reset a user's password."""
    async with async_session_maker() as session:
        try:
            # Find the user
            result = await session.execute(select(User).where(User.username == username))
            user = result.scalars().first()
            
            if not user:
                print(f"User '{username}' not found!")
                return False
            
            # Hash the new password
            hashed_password = hash_password(new_password)
            
            # Update the user's password
            user.hashed_password = hashed_password
            
            # Commit the changes
            await session.commit()
            print(f"Password successfully reset for user '{username}'")
            return True
            
        except Exception as e:
            await session.rollback()
            print(f"Error resetting password: {e}")
            return False

async def main():
    if len(sys.argv) != 3:
        print("Usage: python reset_password.py <username> <new_password>")
        sys.exit(1)
    
    username = sys.argv[1]
    new_password = sys.argv[2]
    
    success = await reset_user_password(username, new_password)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
