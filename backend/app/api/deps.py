from collections.abc import Callable
from typing import Annotated

from fastapi import Cookie, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import decode_session_token
from app.db.session import get_db
from app.models.user import User


def get_current_user(
    database: Annotated[Session, Depends(get_db)],
    session_token: Annotated[str | None, Cookie(alias=get_settings().session_cookie_name)] = None,
) -> User:
    if not session_token:
        raise AppError(401, "UNAUTHENTICATED", "Bạn cần đăng nhập để tiếp tục.")

    user_id = decode_session_token(session_token)
    user = database.get(User, user_id) if user_id else None
    if not user or not user.is_active:
        raise AppError(401, "UNAUTHENTICATED", "Phiên đăng nhập không hợp lệ hoặc đã hết hạn.")
    return user


def require_role(*roles: str) -> Callable[[User], User]:
    """Dependency factory: 403 unless the current user holds one of `roles`."""

    def dependency(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in roles:
            raise AppError(403, "FORBIDDEN", "Bạn không có quyền thực hiện thao tác này.")
        return user

    return dependency
