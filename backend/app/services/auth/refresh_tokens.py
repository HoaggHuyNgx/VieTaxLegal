"""Rotating refresh tokens with reuse detection.

Each login starts a family. Using a refresh token revokes it and issues the next one in the
same family. Presenting an already-revoked token means it leaked (or a stale copy was
replayed), so the whole family is revoked and the user must log in again. A short grace
window tolerates two browser tabs racing on the same cookie.
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import generate_refresh_token, hash_refresh_token
from app.models.refresh_token import RefreshToken
from app.models.user import User

REUSE_GRACE = timedelta(seconds=10)
PURGE_AFTER = timedelta(days=1)  # keep dead rows briefly so reuse is still detectable


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime) -> datetime:
    # SQLite drops tzinfo on read; PostgreSQL keeps it.
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


class RefreshRaceLost(Exception):
    """A token rotated moments ago was presented again: another tab won the race.

    Not an auth failure. The winner's Set-Cookie already holds a valid session, so the
    caller must answer without touching cookies (clearing them would undo the winner's).
    """


def _invalid() -> AppError:
    return AppError(401, "UNAUTHENTICATED", "Phiên đăng nhập không hợp lệ hoặc đã hết hạn.")


def issue_refresh_token(
    database: Session, user: User, remember_me: bool, family_id: UUID | None = None
) -> str:
    settings = get_settings()
    now = _now()
    lifetime = (
        timedelta(days=settings.remember_me_days)
        if remember_me
        else timedelta(hours=settings.session_token_hours)
    )
    raw = generate_refresh_token()
    database.execute(
        delete(RefreshToken)
        .where(RefreshToken.user_id == user.id, RefreshToken.expires_at < now - PURGE_AFTER)
        .execution_options(synchronize_session=False)
    )
    database.add(
        RefreshToken(
            user_id=user.id,
            family_id=family_id or uuid4(),
            token_hash=hash_refresh_token(raw),
            remember_me=remember_me,
            expires_at=now + lifetime,
        )
    )
    database.commit()
    return raw


def _revoke(database: Session, *conditions: object) -> None:
    database.execute(
        update(RefreshToken)
        .where(RefreshToken.revoked_at.is_(None), *conditions)
        .values(revoked_at=_now())
        .execution_options(synchronize_session=False)
    )
    database.commit()


def revoke_all_for_user(database: Session, user_id: UUID) -> None:
    _revoke(database, RefreshToken.user_id == user_id)


def revoke_session(database: Session, raw_token: str | None) -> None:
    """Logout: end the whole login session the presented token belongs to."""
    if not raw_token:
        return
    row = database.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(raw_token))
    )
    if row:
        _revoke(database, RefreshToken.family_id == row.family_id)


def rotate_refresh_token(database: Session, raw_token: str | None) -> tuple[User, str, bool]:
    """Validate and consume a refresh token; return (user, next raw token, remember_me).

    Raises AppError(401) for a dead token and RefreshRaceLost for a just-rotated one.
    """
    if not raw_token:
        raise _invalid()
    row = database.scalar(
        select(RefreshToken)
        .where(RefreshToken.token_hash == hash_refresh_token(raw_token))
        .with_for_update()
    )
    if row is None:
        raise _invalid()

    now = _now()
    if row.revoked_at is not None:
        # A race means a successor is alive in the family; logout/deactivation revoke them all.
        successor_alive = database.scalar(
            select(RefreshToken.id)
            .where(RefreshToken.family_id == row.family_id, RefreshToken.revoked_at.is_(None))
            .limit(1)
        )
        if successor_alive and now - _aware(row.revoked_at) <= REUSE_GRACE:
            raise RefreshRaceLost
        _revoke(database, RefreshToken.family_id == row.family_id)
        raise _invalid()
    if _aware(row.expires_at) <= now:
        raise _invalid()

    user = database.get(User, row.user_id)
    if user is None or not user.is_active:
        _revoke(database, RefreshToken.family_id == row.family_id)
        raise _invalid()

    remember_me = row.remember_me
    row.revoked_at = now
    database.flush()
    return user, issue_refresh_token(database, user, remember_me, row.family_id), remember_me
