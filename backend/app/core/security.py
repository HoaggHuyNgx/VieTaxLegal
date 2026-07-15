from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import get_settings

password_hash = PasswordHash.recommended()
dummy_password_hash = password_hash.hash("not-a-real-password")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def verify_dummy_password(password: str) -> None:
    """Spend the same password-verification cost when an account is unavailable."""
    password_hash.verify(password, dummy_password_hash)


def create_session_token(user_id: UUID, remember_me: bool) -> str:
    settings = get_settings()
    lifetime = (
        timedelta(days=settings.remember_me_days)
        if remember_me
        else timedelta(hours=settings.session_token_hours)
    )
    expires_at = datetime.now(timezone.utc) + lifetime
    payload = {"sub": str(user_id), "type": "session", "exp": expires_at}
    return jwt.encode(
        payload, settings.jwt_secret.get_secret_value(), algorithm=settings.jwt_algorithm
    )


def decode_session_token(token: str) -> UUID | None:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("type") != "session" or not payload.get("sub"):
            return None
        return UUID(payload["sub"])
    except (InvalidTokenError, ValueError):
        return None
