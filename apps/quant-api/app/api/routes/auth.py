
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_user,
    get_db,
    get_settings_from_request,
    require_trusted_origin,
)
from app.api.errors import ApiError, success
from app.core.config import Settings
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.auth import AuthPayload, DeleteAccountRequest, LoginRequest, RegisterRequest, UserResponse
from app.services.auth import (
    authenticate_user,
    create_refresh_session,
    register_user,
    revoke_refresh_session,
    rotate_refresh_session,
    verify_password,
)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


def user_payload(user: User) -> dict[str, object]:
    return UserResponse.model_validate(user).model_dump(mode="json")


def auth_payload(user: User, settings: Settings) -> dict[str, object]:
    return AuthPayload(
        access_token=create_access_token(user.id, settings),
        expires_in=settings.access_token_ttl_seconds,
        user=UserResponse.model_validate(user),
    ).model_dump(mode="json")


def set_refresh_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        max_age=settings.refresh_token_ttl_seconds,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_same_site,
        path=settings.cookie_path,
    )


def clear_refresh_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        key=settings.cookie_name,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_same_site,
        path=settings.cookie_path,
    )


def request_metadata(request: Request) -> tuple[str | None, str | None]:
    return request.headers.get("user-agent"), request.client.host if request.client else None


@router.post("/register", status_code=201, dependencies=[Depends(require_trusted_origin)])
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    user = register_user(db, payload)
    return success({"user": user_payload(user)}, "Account created")


@router.post("/login", dependencies=[Depends(require_trusted_origin)])
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_from_request),
) -> dict[str, object]:
    user = authenticate_user(db, payload)
    user_agent, ip_address = request_metadata(request)
    refresh_token = create_refresh_session(db, user, settings, user_agent, ip_address)
    set_refresh_cookie(response, refresh_token, settings)
    return success(auth_payload(user, settings), "Signed in")


@router.post("/refresh", dependencies=[Depends(require_trusted_origin)])
def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_from_request),
) -> dict[str, object]:
    raw_token = request.cookies.get(settings.cookie_name)
    if not raw_token:
        raise ApiError(401, "REFRESH_TOKEN_MISSING", "Refresh token is required")
    user, refreshed_token = rotate_refresh_session(db, raw_token, settings)
    set_refresh_cookie(response, refreshed_token, settings)
    return success(auth_payload(user, settings), "Session refreshed")


@router.post("/logout", dependencies=[Depends(require_trusted_origin)])
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_from_request),
) -> dict[str, object]:
    revoke_refresh_session(db, request.cookies.get(settings.cookie_name), settings)
    clear_refresh_cookie(response, settings)
    return success({}, "Signed out")


@router.get("/me")
def get_me(user: User = Depends(get_current_user)) -> dict[str, object]:
    return success(user_payload(user))


@router.delete("/account", dependencies=[Depends(require_trusted_origin)])
def delete_account(
    payload: DeleteAccountRequest,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_from_request),
    user: User = Depends(get_current_user),
) -> dict[str, object]:
    if not verify_password(payload.password, user.password_hash):
        raise ApiError(401, "INVALID_CREDENTIALS", "Password confirmation failed")
    db.delete(user)
    db.commit()
    clear_refresh_cookie(response, settings)
    return success({}, "Account deleted")
