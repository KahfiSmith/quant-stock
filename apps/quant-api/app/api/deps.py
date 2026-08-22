from collections.abc import Generator

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.api.errors import ApiError
from app.core.config import Settings
from app.core.security import decode_access_token
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_settings_from_request(request: Request) -> Settings:
    return request.app.state.settings


def get_db(request: Request) -> Generator[Session, None, None]:
    db = request.app.state.database.session()
    try:
        yield db
    finally:
        db.close()


def require_trusted_origin(request: Request, settings: Settings = Depends(get_settings_from_request)) -> None:
    origin = request.headers.get("origin")
    if origin and origin.rstrip("/") not in settings.allowed_origins:
        raise ApiError(403, "FORBIDDEN", "Origin not allowed")


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_from_request),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise ApiError(401, "ACCESS_TOKEN_MISSING", "Access token is required")

    try:
        user_id = decode_access_token(credentials.credentials, settings)
    except ValueError as error:
        raise ApiError(401, "ACCESS_TOKEN_INVALID", "Access token is invalid") from error

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise ApiError(401, "UNAUTHORIZED", "Authentication is required")
    return user
