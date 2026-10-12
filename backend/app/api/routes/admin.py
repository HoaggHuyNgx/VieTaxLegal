from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.user import ROLE_ADMIN, User
from app.schemas.admin import AdminUserResponse, AdminUserUpdate
from app.services import admin as admin_service

router = APIRouter(prefix="/admin", tags=["Admin"])
AdminUser = Annotated[User, Depends(require_role(ROLE_ADMIN))]


@router.get("/users", response_model=list[AdminUserResponse])
def list_users(
    _: AdminUser,
    database: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[User]:
    return admin_service.list_users(database, limit, offset)


@router.patch("/users/{user_id}", response_model=AdminUserResponse)
def update_user(
    user_id: UUID,
    payload: AdminUserUpdate,
    admin: AdminUser,
    database: Annotated[Session, Depends(get_db)],
) -> User:
    return admin_service.update_user(database, admin, user_id, payload)
