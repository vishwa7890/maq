#!/usr/bin/env python3
"""
Script to test password verification for a user.
Usage: python test_password.py <username> <password_to_test>
"""
import asyncio
import sys
from pathlib import Path
import os

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = backend_dir / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except Exception:
    pass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.base import async_session_maker
from models.user import User
from app.auth import verify_password, hash_password

async def test_password(username: str, password: str):
    """Test if a password matches for a user."""
    if not os.getenv("DATABASE_URL"):
        print("Error: DATABASE_URL is not set.")
        return False
    
    async with async_session_maker() as session:
        try:
            # Find the user
            result = await session.execute(select(User).where(User.username == username))
            user = result.scalars().first()
            
            if not user:
                print(f"❌ User '{username}' not found!")
                return False
            
            print(f"✅ User found: {username}")
            print(f"   ID: {user.id}")
            print(f"   Email: {user.email}")
            print(f"   Role: {user.role}")
            print(f"   Quotes Used: {user.quotes_used}")
            print(f"\n🔐 Testing password...")
            
            # Test the password
            is_valid = verify_password(password, user.hashed_password)
            
            if is_valid:
                print(f"✅ Password is CORRECT!")
            else:
                print(f"❌ Password is INCORRECT!")
                print(f"\n💡 To reset password, run:")
                print(f"   python reset_password.py {username} <new_password>")
            
            return is_valid
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

async def main():
    if len(sys.argv) != 3:
        print("Usage: python test_password.py <username> <password_to_test>")
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2]
    
    success = await test_password(username, password)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
