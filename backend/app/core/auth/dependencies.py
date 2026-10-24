import uuid

from fastapi import Cookie, HTTPException, Request, status
from jose import JWTError

from app.core.auth.service import decode_access_token


async def get_current_user_id(
    request: Request,
    access_token: str | None = Cookie(default=None),
) -> uuid.UUID:
    token = access_token
    if token is None:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    try:
        payload = decode_access_token(token)
        return uuid.UUID(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
