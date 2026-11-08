"""Map a validated Google identity onto a local user: sign in, create, or link."""

import re
import secrets
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.oauth_identity import PROVIDER_GOOGLE, OAuthIdentity
from app.models.user import User
from app.services.google_oauth import GoogleClaims, google_failed

USERNAME_TRIES = 10


def _find_identity(database: Session, subject: str) -> OAuthIdentity | None:
    return database.scalar(
        select(OAuthIdentity).where(
            OAuthIdentity.provider == PROVIDER_GOOGLE, OAuthIdentity.subject == subject
        )
    )


def _username_base(email: str) -> str:
    base = re.sub(r"[^a-z0-9_]", "_", email.split("@")[0].lower())[:20]
    return base if len(base) >= 3 else f"user_{base}"


def _free_username(database: Session, email: str) -> str:
    base = _username_base(email)
    candidate = base
    for _ in range(USERNAME_TRIES):
        if not database.scalar(select(User.id).where(User.username == candidate)):
            return candidate
        candidate = f"{base}_{secrets.token_hex(2)}"  # random, so counts are not revealed
    raise AppError(409, "REGISTRATION_CONFLICT", "Không thể tạo tài khoản. Vui lòng thử lại.")


def _create_user(database: Session, claims: GoogleClaims) -> User:
    full_name = (claims.name or claims.email.split("@")[0]).strip()[:120]
    user = User(
        email=claims.email,
        username=_free_username(database, claims.email),
        # Registration requires >= 2 characters; a whole email address always has at least 3.
        full_name=full_name if len(full_name) >= 2 else claims.email[:120],
        password_hash=None,
        terms_accepted_at=datetime.now(timezone.utc),  # the Google button states the consent
    )
    user.oauth_identities.append(OAuthIdentity(provider=PROVIDER_GOOGLE, subject=claims.subject))
    database.add(user)
    try:
        database.commit()
    except IntegrityError:
        database.rollback()
        raise AppError(
            409, "REGISTRATION_CONFLICT", "Không thể tạo tài khoản. Vui lòng thử lại."
        ) from None
    database.refresh(user)
    return user


def sign_in_with_google(database: Session, claims: GoogleClaims) -> User:
    """Known `sub` signs in. A new email creates an account. An email that already belongs to a
    password account is refused: it was never verified, so linking it automatically would let
    whoever registered it first keep access. The owner links Google from settings instead."""
    identity = _find_identity(database, claims.subject)
    if identity:
        user = database.get(User, identity.user_id)
        if user is None or not user.is_active:
            raise google_failed()  # same answer as any failure: no account probing
        return user

    if database.scalar(select(User.id).where(User.email == claims.email)):
        raise AppError(
            409,
            "GOOGLE_EMAIL_NEEDS_PASSWORD_LOGIN",
            "Email này đã có tài khoản mật khẩu. Hãy đăng nhập bằng mật khẩu rồi liên kết Google.",
        )
    return _create_user(database, claims)


def link_google(database: Session, user: User, claims: GoogleClaims) -> None:
    if not user.is_active:
        raise google_failed()
    if user.google_linked:
        raise AppError(409, "GOOGLE_ALREADY_LINKED", "Tài khoản đã liên kết với Google.")
    if _find_identity(database, claims.subject):
        raise AppError(
            409, "GOOGLE_ACCOUNT_TAKEN", "Tài khoản Google này đã liên kết với người dùng khác."
        )
    database.add(OAuthIdentity(user_id=user.id, provider=PROVIDER_GOOGLE, subject=claims.subject))
    try:
        database.commit()
    except IntegrityError:
        database.rollback()
        raise AppError(
            409, "GOOGLE_ACCOUNT_TAKEN", "Tài khoản Google này đã liên kết với người dùng khác."
        ) from None
