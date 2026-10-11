from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import hash_password, verify_dummy_password, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.login_throttle import get_login_throttle


def get_registration_conflict(database: Session, payload: RegisterRequest) -> AppError | None:
    if database.scalar(select(User.id).where(User.email == payload.email)):
        return AppError(
            409, "EMAIL_TAKEN", "Email này đã được sử dụng.", {"email": "Email đã tồn tại."}
        )

    if database.scalar(select(User.id).where(User.username == payload.username)):
        return AppError(
            409,
            "USERNAME_TAKEN",
            "Tên tài khoản này đã được sử dụng.",
            {"username": "Tên tài khoản đã tồn tại."},
        )

    return None


def register_user(database: Session, payload: RegisterRequest) -> User:
    conflict = get_registration_conflict(database, payload)
    if conflict:
        raise conflict

    user = User(
        email=str(payload.email),
        username=payload.username,
        full_name=payload.full_name,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        terms_accepted_at=datetime.now(timezone.utc),
    )
    database.add(user)
    try:
        database.commit()
    except IntegrityError:
        database.rollback()
        conflict = get_registration_conflict(database, payload)
        if conflict:
            raise conflict from None
        raise AppError(
            409,
            "REGISTRATION_CONFLICT",
            "Không thể tạo tài khoản. Vui lòng thử lại.",
        ) from None

    database.refresh(user)
    return user


def authenticate_user(database: Session, payload: LoginRequest) -> User:
    user = database.scalar(
        select(User).where(
            or_(User.email == payload.identifier, User.username == payload.identifier)
        )
    )
    if not user or not user.is_active:
        verify_dummy_password(payload.password)
        raise AppError(401, "INVALID_CREDENTIALS", "Email/tên tài khoản hoặc mật khẩu không đúng.")

    if not verify_password(payload.password, user.password_hash):
        raise AppError(401, "INVALID_CREDENTIALS", "Email/tên tài khoản hoặc mật khẩu không đúng.")
    return user


def login_user(database: Session, payload: LoginRequest, client_host: str) -> User:
    """Authenticate, rejecting early once a client/identifier pair has failed too often.

    Keyed by client and identifier so one source cannot grind a single account, while a
    stranger still cannot lock a victim out from every other address.
    """
    throttle = get_login_throttle()
    key = f"{client_host}|{payload.identifier}"
    throttle.check(key)
    try:
        user = authenticate_user(database, payload)
    except AppError:
        throttle.record_failure(key)
        raise
    throttle.reset(key)
    return user
