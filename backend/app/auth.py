from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from models import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.base import get_db
import os
import logging

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

# Password helpers
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# JWT helpers
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# User DB helpers
async def get_user_by_username(session: AsyncSession, username: str):
    """Get user by username with fresh data."""
    try:
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalars().first()
        if user:
            await session.refresh(user)
        return user
    except Exception as e:
        logger.error(f"Error fetching user by username {username}: {e}")
        return None

async def get_user_by_email(session: AsyncSession, email: str):
    result = await session.execute(select(User).filter(User.email == email))
    return result.scalars().first()

# Authentication dependency
async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Dependency to get the current user from the JWT token in the request cookies."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Get token from cookies first
    token = request.cookies.get("access_token")
    try:
        # Safe debug: log whether cookie present and its length only
        token_len = len(token) if token else 0
        logger.info(f"Auth cookie present: {bool(token)}, length: {token_len}")
    except Exception:
        pass
    if not token:
        # Fallback to Authorization header
        auth = request.headers.get("Authorization") or request.headers.get("authorization")
        if auth and auth.lower().startswith("bearer "):
            token = auth[7:]
        else:
            raise credentials_exception
    else:
        # Remove 'Bearer ' prefix if present in cookie
        if token.startswith("Bearer "):
            token = token[7:]
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.warning("JWT decoded but no 'sub' in payload: %s", payload)
            raise credentials_exception
    except JWTError as e:
        logger.warning("JWT decode failed: %s", str(e))
        raise credentials_exception
        
    user = await get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
        
    return user