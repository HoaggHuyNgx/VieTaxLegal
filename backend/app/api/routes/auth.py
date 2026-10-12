from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.errors import AppError, app_error_handler
from app.core.security import create_session_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, UserResponse
from app.services.auth import login_user, register_user
from app.services.login_throttle import get_register_throttle
from app.services.refresh_tokens import (
    issue_refresh_token,
    revoke_session,
    rotate_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# The refresh cookie is only ever needed by /auth/refresh and /auth/logout.
REFRESH_COOKIE_PATH = f"{get_settings().api_prefix}/auth"


def client_host(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def set_auth_cookies(response: Response, user: User, refresh_token: str, remember_me: bool) -> None:
    """Short-lived access JWT (session cookie) + rotating refresh token (path-scoped)."""
    settings = get_settings()
    response.set_cookie(
        key=settings.session_cookie_name,
        value=create_session_token(user.id),
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        path="/",
    )
    refresh_options: dict[str, object] = {
        "key": settings.refresh_cookie_name,
        "value": refresh_token,
        "httponly": True,
        "secure": settings.is_production,
        "samesite": "lax",
        "path": REFRESH_COOKIE_PATH,
    }
    if remember_me:
        refresh_options["max_age"] = settings.remember_me_days * 24 * 60 * 60
    response.set_cookie(**refresh_options)


def clear_auth_cookies(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(settings.session_cookie_name, path="/", httponly=True, samesite="lax")
    response.delete_cookie(
        settings.refresh_cookie_name, path=REFRESH_COOKIE_PATH, httponly=True, samesite="lax"
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    database: Annotated[Session, Depends(get_db)],
) -> User:
    throttle = get_register_throttle()
    throttle.check(client_host(request))
    throttle.record_failure(client_host(request))  # counts every attempt, not just failures
    user = register_user(database, payload)
    set_auth_cookies(response, user, issue_refresh_token(database, user, False), False)
    return user


@router.post("/login", response_model=UserResponse)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    database: Annotated[Session, Depends(get_db)],
) -> User:
    user = login_user(database, payload, client_host(request))
    refresh_token = issue_refresh_token(database, user, payload.remember_me)
    set_auth_cookies(response, user, refresh_token, payload.remember_me)
    return user


@router.post("/refresh", response_model=UserResponse)
def refresh(
    request: Request,
    response: Response,
    database: Annotated[Session, Depends(get_db)],
    refresh_token: Annotated[str | None, Cookie(alias=get_settings().refresh_cookie_name)] = None,
) -> User | Response:
    try:
        user, next_token, remember_me = rotate_refresh_token(database, refresh_token)
    except AppError as error:
        # Headers set on the injected `response` are dropped when an error is raised, so
        # build the error response here to clear the dead cookies on it.
        failure = app_error_handler(request, error)
        clear_auth_cookies(failure)
        return failure
    set_auth_cookies(response, user, next_token, remember_me)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    database: Annotated[Session, Depends(get_db)],
    refresh_token: Annotated[str | None, Cookie(alias=get_settings().refresh_cookie_name)] = None,
) -> None:
    revoke_session(database, refresh_token)
    clear_auth_cookies(response)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user
