"""Prove control of an email address before an account is registered with it.

send_code mails a 6-digit code; verify_code swaps a correct code for a short-lived signed
proof that /auth/register requires. The code has little entropy, so security rests on the
10-minute expiry, the attempt cap and the send limits, not on hashing.
"""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import InvalidTokenError
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.email_otp import EmailOtp
from app.models.user import User
from app.services import mailer

CODE_TTL = timedelta(minutes=10)
RESEND_COOLDOWN = timedelta(seconds=60)
MAX_SENDS_PER_HOUR = 5
MAX_ATTEMPTS = 5
PROOF_TTL = timedelta(minutes=15)
PURGE_AFTER = timedelta(days=1)
PROOF_TYPE = "email_proof"  # never accepted as an access token (that needs type "access")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime) -> datetime:
    # SQLite drops tzinfo on read; PostgreSQL keeps it.
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _hash_code(email: str, code: str) -> str:
    key = get_settings().jwt_secret.get_secret_value().encode()
    return hmac.new(key, f"{email}:{code}".encode(), hashlib.sha256).hexdigest()


def _rate_limited() -> AppError:
    return AppError(429, "OTP_RATE_LIMITED", "Bạn yêu cầu mã quá nhiều lần. Vui lòng thử lại sau.")


def _sent_since(database: Session, email: str, since: datetime) -> int:
    return database.scalar(
        select(func.count())
        .select_from(EmailOtp)
        .where(EmailOtp.email == email, EmailOtp.created_at > since)
    )


def send_code(database: Session, email: str) -> None:
    now = _now()
    database.execute(delete(EmailOtp).where(EmailOtp.created_at < now - PURGE_AFTER))

    if database.scalar(select(User.id).where(User.email == email)):
        raise AppError(
            409, "EMAIL_TAKEN", "Email này đã được sử dụng.", {"email": "Email đã tồn tại."}
        )

    code = f"{secrets.randbelow(10**6):06d}"
    row = EmailOtp(
        email=email, code_hash=_hash_code(email, code), expires_at=now + CODE_TTL, created_at=now
    )
    database.add(row)
    database.commit()
    # Limits are counted after our own row is committed, so of two racing requests the one that
    # counts last always sees both rows: at most one of them gets a mail.
    if (
        _sent_since(database, email, now - RESEND_COOLDOWN) > 1
        or _sent_since(database, email, now - timedelta(hours=1)) > MAX_SENDS_PER_HOUR
    ):
        database.delete(row)
        database.commit()
        raise _rate_limited()
    try:
        mailer.send_mail(
            email,
            "Mã xác minh email VieTaxLegal",
            f"Mã xác minh của bạn là: {code}\n\n"
            "Mã có hiệu lực trong 10 phút. Nếu bạn không yêu cầu, hãy bỏ qua email này.",
        )
    except AppError:
        database.delete(row)  # a failed send must not start the resend cooldown
        database.commit()
        raise


def create_email_proof(email: str) -> str:
    settings = get_settings()
    return jwt.encode(
        {"type": PROOF_TYPE, "email": email, "exp": _now() + PROOF_TTL},
        settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def verify_code(database: Session, email: str, code: str) -> str:
    """Return a proof for `email` if `code` matches the newest unused code mailed to it."""
    now = _now()
    row = database.scalar(
        select(EmailOtp)
        .where(EmailOtp.email == email, EmailOtp.consumed_at.is_(None))
        .order_by(EmailOtp.created_at.desc())
    )
    if row is None:
        raise AppError(400, "OTP_INVALID", "Mã xác minh không đúng.")
    if _aware(row.expires_at) <= now:
        raise AppError(400, "OTP_EXPIRED", "Mã xác minh đã hết hạn. Hãy yêu cầu mã mới.")
    if row.attempts >= MAX_ATTEMPTS:
        raise AppError(429, "OTP_TOO_MANY_ATTEMPTS", "Nhập sai quá nhiều lần. Hãy yêu cầu mã mới.")
    if not hmac.compare_digest(row.code_hash, _hash_code(email, code)):
        row.attempts += 1
        database.commit()
        raise AppError(400, "OTP_INVALID", "Mã xác minh không đúng.")

    row.consumed_at = now
    database.commit()
    return create_email_proof(email)


def require_proof(proof: str, email: str) -> None:
    settings = get_settings()
    try:
        claims = jwt.decode(
            proof, settings.jwt_secret.get_secret_value(), algorithms=[settings.jwt_algorithm]
        )
    except InvalidTokenError:
        claims = {}
    if claims.get("type") != PROOF_TYPE or claims.get("email") != email:
        raise AppError(403, "EMAIL_NOT_VERIFIED", "Bạn cần xác minh email trước khi đăng ký.")
