import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user_id
from app.core.auth.models import RefreshToken, User
from app.core.auth.schemas import LoginRequest, LoginResponse, RegisterRequest, UserResponse
from app.core.auth.service import (
    authenticate_user,
    create_access_token,
    create_refresh_token_raw,
    get_refresh_token_record,
    hash_password,
    hash_refresh_token,
)
from app.core.config import settings
from app.core.db import get_session

router = APIRouter(prefix="/api/auth", tags=["auth"])

_COOKIE_KWARGS = dict(httponly=True, samesite="lax", secure=False)


def _set_access_cookie(response: Response, token: str) -> None:
    response.set_cookie("access_token", token, **_COOKIE_KWARGS)


def _set_refresh_cookie(response: Response, token: str) -> None:
    max_age = settings.refresh_token_expire_days * 86400
    response.set_cookie("refresh_token", token, max_age=max_age, **_COOKIE_KWARGS)


def _clear_cookies(response: Response) -> None:
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")


@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    response: Response,
    session: AsyncSession = Depends(get_session),
):
    existing = await session.execute(select(User).where(User.email == body.email))
    if existing.scalars().first() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(id=uuid.uuid4(), email=body.email, password_hash=hash_password(body.password))
    session.add(user)
    await session.commit()
    await session.refresh(user)

    access_token = create_access_token(user.id)
    raw_refresh = create_refresh_token_raw()
    token_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_refresh),
        expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days),
    )
    session.add(token_record)
    await session.commit()

    _set_access_cookie(response, access_token)
    _set_refresh_cookie(response, raw_refresh)
    return LoginResponse(user=UserResponse.model_validate(user))


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_session),
):
    user = await authenticate_user(session, body.email, body.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    access_token = create_access_token(user.id)
    raw_refresh = create_refresh_token_raw()

    token_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_refresh),
        expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days),
    )
    session.add(token_record)
    await session.commit()

    _set_access_cookie(response, access_token)
    _set_refresh_cookie(response, raw_refresh)

    return LoginResponse(user=UserResponse.model_validate(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    session: AsyncSession = Depends(get_session),
):
    if refresh_token:
        record = await get_refresh_token_record(session, refresh_token)
        if record and record.revoked_at is None:
            record.revoked_at = datetime.now(UTC)
            await session.commit()

    _clear_cookies(response)


@router.post("/refresh")
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    session: AsyncSession = Depends(get_session),
):
    if refresh_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    record = await get_refresh_token_record(session, refresh_token)

    if (
        record is None
        or record.revoked_at is not None
        or record.expires_at < datetime.now(UTC)
    ):
        _clear_cookies(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    new_access = create_access_token(record.user_id)
    _set_access_cookie(response, new_access)
    return {}


@router.get("/me", response_model=UserResponse)
async def me(
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(User).where(User.id == current_user_id))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return UserResponse.model_validate(user)
