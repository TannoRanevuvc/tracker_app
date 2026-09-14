import uuid

from fastapi import Cookie, HTTPException, status
from jose import JWTError

from app.core.auth.service import decode_access_token


async def get_current_user_id(
    access_token: str | None = Cookie(default=None),
) -> uuid.UUID:
    if access_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    try:
        payload = decode_access_token(access_token)
        return uuid.UUID(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
