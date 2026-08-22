import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.errors import ApiError
from app.core.config import Settings
from app.core.security import (
    hash_password,
    hash_refresh_token,
    new_refresh_token,
    verify_password,
)
from app.models.auth_session import AuthSession, RefreshToken
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest


def utc_now() -> datetime:
    return datetime.now(UTC)


def as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def register_user(db: Session, payload: RegisterRequest) -> User:
    email = str(payload.email).lower()
    existing = db.scalar(select(User).where(User.email == email))
    if existing is not None:
        raise ApiError(409, "EMAIL_ALREADY_REGISTERED", "Email is already registered")

    user = User(email=email, name=payload.name.strip(), password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, payload: LoginRequest) -> User:
    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise ApiError(401, "INVALID_CREDENTIALS", "Invalid email or password")
    if not user.is_active:
        raise ApiError(403, "ACCOUNT_DISABLED", "Account is disabled")
    return user


def create_refresh_session(
    db: Session,
    user: User,
    settings: Settings,
    user_agent: str | None,
    ip_address: str | None,
) -> str:
    expires_at = utc_now() + timedelta(seconds=settings.refresh_token_ttl_seconds)
    refresh_token = new_refresh_token()
    session = AuthSession(
        user_id=user.id,
        family_id=secrets.token_urlsafe(24),
        user_agent=user_agent,
        ip_address=ip_address,
        expires_at=expires_at,
    )
    session.refresh_tokens.append(
        RefreshToken(
            token_hash=hash_refresh_token(refresh_token, settings),
            expires_at=expires_at,
        )
    )
    db.add(session)
    db.commit()
    return refresh_token


def rotate_refresh_session(db: Session, raw_token: str, settings: Settings) -> tuple[User, str]:
    token_hash = hash_refresh_token(raw_token, settings)
    token_record = db.scalar(
        select(RefreshToken)
        .options(joinedload(RefreshToken.session).joinedload(AuthSession.user))
        .where(RefreshToken.token_hash == token_hash)
    )
    if token_record is None:
        raise ApiError(401, "REFRESH_TOKEN_INVALID", "Refresh token is invalid")

    auth_session = db.scalar(
        select(AuthSession).where(AuthSession.id == token_record.session_id).with_for_update()
    )
    if auth_session is None or auth_session.revoked_at is not None:
        raise ApiError(401, "SESSION_REVOKED", "Session has been revoked")

    now = utc_now()
    if token_record.used_at is not None:
        auth_session.revoked_at = now
        db.commit()
        raise ApiError(401, "REFRESH_TOKEN_REUSED", "Refresh token reuse detected")
    if as_utc(token_record.expires_at) <= now or as_utc(auth_session.expires_at) <= now:
        auth_session.revoked_at = now
        db.commit()
        raise ApiError(401, "REFRESH_TOKEN_EXPIRED", "Refresh token has expired")

    token_record.used_at = now
    new_token = new_refresh_token()
    auth_session.refresh_tokens.append(
        RefreshToken(
            token_hash=hash_refresh_token(new_token, settings),
            expires_at=auth_session.expires_at,
        )
    )
    db.commit()
    return token_record.session.user, new_token


def revoke_refresh_session(db: Session, raw_token: str | None, settings: Settings) -> None:
    if not raw_token:
        return
    token_hash = hash_refresh_token(raw_token, settings)
    token_record = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    if token_record is None:
        return
    auth_session = db.get(AuthSession, token_record.session_id)
    if auth_session is not None and auth_session.revoked_at is None:
        auth_session.revoked_at = utc_now()
        db.commit()
