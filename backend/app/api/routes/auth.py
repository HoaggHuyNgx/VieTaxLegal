from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.security import create_session_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, UserResponse
from app.services.auth import login_user, register_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


def set_session_cookie(response: Response, user: User, remember_me: bool) -> None:
    settings = get_settings()
    cookie_options: dict[str, object] = {
        "key": settings.session_cookie_name,
        "value": create_session_token(user.id, remember_me),
        "httponly": True,
        "secure": settings.is_production,
        "samesite": "lax",
        "path": "/",
    }
    if remember_me:
        cookie_options["max_age"] = settings.remember_me_days * 24 * 60 * 60
    response.set_cookie(**cookie_options)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    response: Response,
    database: Annotated[Session, Depends(get_db)],
) -> User:
    user = register_user(database, payload)
    set_session_cookie(response, user, remember_me=False)
    return user


@router.post("/login", response_model=UserResponse)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    database: Annotated[Session, Depends(get_db)],
) -> User:
    user = login_user(database, payload, request.client.host if request.client else "unknown")
    set_session_cookie(response, user, remember_me=payload.remember_me)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(settings.session_cookie_name, path="/", httponly=True, samesite="lax")


@router.get("/me", response_model=UserResponse)
def get_me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user
