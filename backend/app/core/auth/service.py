import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import bcrypt as _bcrypt
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.auth.models import RefreshToken, User


def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt(12)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(
    user_id: uuid.UUID,
    expires_delta: timedelta | None = None,
) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    expire = datetime.now(UTC) + expires_delta
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=["HS256"])


def create_refresh_token_raw() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


async def get_refresh_token_record(
    session: AsyncSession, raw_token: str
) -> RefreshToken | None:
    token_hash = hash_refresh_token(raw_token)
    result = await session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    return result.scalars().first()


async def authenticate_user(session: AsyncSession, email: str, password: str):
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user
