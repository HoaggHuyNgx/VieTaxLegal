from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.user import ROLES, User
from app.schemas.admin import AdminUserUpdate
from app.services.refresh_tokens import revoke_all_for_user


def list_users(database: Session, limit: int, offset: int) -> list[User]:
    query = select(User).order_by(User.created_at, User.id).limit(limit).offset(offset)
    return list(database.scalars(query))


def update_user(database: Session, admin: User, user_id: UUID, payload: AdminUserUpdate) -> User:
    if user_id == admin.id:
        raise AppError(409, "CANNOT_MODIFY_SELF", "Bạn không thể tự thay đổi quyền của mình.")
    user = database.get(User, user_id)
    if user is None:
        raise AppError(404, "USER_NOT_FOUND", "Không tìm thấy người dùng.")

    if payload.role is not None:
        if payload.role not in ROLES:
            raise AppError(
                422, "VALIDATION_ERROR", "Vai trò không hợp lệ.", {"role": "Vai trò không hợp lệ."}
            )
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active
    database.commit()
    if payload.is_active is False:
        revoke_all_for_user(database, user.id)  # access JWT still dies on its own in minutes
    database.refresh(user)
    return user
