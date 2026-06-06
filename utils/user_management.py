import os
import asyncpg
import logging
from passlib.context import CryptContext
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# --- Database Connection ---
DATABASE_URL = os.getenv("DATABASE_URL")


class Database:
    """Manages the database connection pool."""

    pool: Optional[asyncpg.Pool] = None

    @classmethod
    async def connect(cls):
        """Creates the database connection pool."""
        if not cls.pool:
            try:
                cls.pool = await asyncpg.create_pool(DATABASE_URL, command_timeout=5)
            except Exception as e:
                logger.warning(
                    f"Database connection failed: {e}. Running without database."
                )
                cls.pool = None

    @classmethod
    async def disconnect(cls):
        """Closes the database connection pool."""
        if cls.pool:
            await cls.pool.close()
            cls.pool = None

    @classmethod
    async def fetch(cls, query: str, *args):
        """Executes a query and returns the results."""
        if not cls.pool:
            await cls.connect()
        async with cls.pool.acquire() as connection:
            return await connection.fetch(query, *args)

    @classmethod
    async def execute(cls, query: str, *args):
        """Executes a query without returning results."""
        if not cls.pool:
            await cls.connect()
        async with cls.pool.acquire() as connection:
            await connection.execute(query, *args)


# --- Password Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hashes a plain-text password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain-text password against a hashed one."""
    return pwd_context.verify(plain_password, hashed_password)


# --- User Management Functions ---
async def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Retrieves a user from the database by their username."""
    query = "SELECT * FROM users WHERE username = $1"
    rows = await Database.fetch(query, username)
    if rows:
        return dict(rows[0])
    return None


async def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves a user from the database by their ID."""
    query = "SELECT * FROM users WHERE id = $1"
    rows = await Database.fetch(query, user_id)
    if rows:
        return dict(rows[0])
    return None


async def create_user(username: str, password: str) -> Dict[str, Any]:
    """Creates a new user in the database."""
    hashed_password = hash_password(password)
    query = """
        INSERT INTO users (username, hashed_password)
        VALUES ($1, $2)
        RETURNING id, username, created_at
    """
    try:
        new_user_record = await Database.fetch(query, username, hashed_password)
        return dict(new_user_record[0])
    except asyncpg.exceptions.UniqueViolationError:
        # This error is raised if the username already exists.
        return None

# JWT auth helpers
import jwt
from jwt import PyJWTError
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer

JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET or len(JWT_SECRET) < 32:
    raise RuntimeError(
        "CRITICAL: JWT_SECRET environment variable not set or too short (< 32 bytes). "
        "Generate with: openssl rand -base64 48"
    )
JWT_ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_user_id_from_token(token: str) -> Optional[str]:
    """Decode JWT token and return user_id."""
    if not token:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except PyJWTError:
        return None

async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """Dependency to get current user from JWT token."""
    user_id = get_user_id_from_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id
