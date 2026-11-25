import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import get_settings
from app.core.errors import AppError

SMTP_TIMEOUT_SECONDS = 15


def send_mail(to: str, subject: str, body: str) -> None:
    """Send a plain-text mail through the configured SMTP server (stdlib only)."""
    settings = get_settings()
    if not settings.email_enabled:
        raise AppError(503, "EMAIL_NOT_CONFIGURED", "Dịch vụ gửi email chưa được cấu hình.")

    message = EmailMessage()
    message["From"] = settings.smtp_from or settings.smtp_user
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    host, port = settings.smtp_host, settings.smtp_port
    try:
        if port == 465:
            server = smtplib.SMTP_SSL(
                host, port, timeout=SMTP_TIMEOUT_SECONDS, context=ssl.create_default_context()
            )
        else:
            server = smtplib.SMTP(host, port, timeout=SMTP_TIMEOUT_SECONDS)
        with server:
            if port != 465:
                server.starttls(context=ssl.create_default_context())
            if settings.smtp_user and settings.smtp_password:
                server.login(settings.smtp_user, settings.smtp_password.get_secret_value())
            server.send_message(message)
    except (OSError, smtplib.SMTPException):
        # Not logged with details: the exception text can echo the account name.
        raise AppError(502, "EMAIL_SEND_FAILED", "Không thể gửi email. Vui lòng thử lại.") from None
