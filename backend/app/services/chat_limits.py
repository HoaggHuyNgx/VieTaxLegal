"""Chat quotas and stale-reply expiry (database-backed, so they hold across processes)."""

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.chat import ChatUsageEvent, Message

# A pending reply older than this belongs to a stream that died without finalizing.
PENDING_REPLY_TIMEOUT = timedelta(minutes=5)


def expire_stale_pending(database: Session, conversation_id: UUID, now: datetime) -> None:
    """Mark abandoned pending replies as failed so a crashed stream cannot lock the conversation."""
    database.execute(
        update(Message)
        .where(
            Message.conversation_id == conversation_id,
            Message.role == "assistant",
            Message.status == "pending",
            Message.created_at < now - PENDING_REPLY_TIMEOUT,
        )
        .values(status="failed", updated_at=now)
    )


def enforce_rate_limits(database: Session, user_id: UUID, now: datetime) -> None:
    settings = get_settings()
    count_statement = select(func.count(ChatUsageEvent.id)).where(ChatUsageEvent.user_id == user_id)
    minute_count = database.scalar(
        count_statement.where(ChatUsageEvent.created_at >= now - timedelta(minutes=1))
    )
    if (minute_count or 0) >= settings.chat_rate_limit_per_minute:
        raise AppError(
            429,
            "CHAT_RATE_LIMITED",
            "Bạn gửi câu hỏi quá nhanh. Vui lòng thử lại sau ít phút.",
        )

    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    daily_count = database.scalar(count_statement.where(ChatUsageEvent.created_at >= start_of_day))
    if (daily_count or 0) >= settings.chat_daily_message_limit:
        raise AppError(
            429,
            "CHAT_DAILY_LIMIT_REACHED",
            "Bạn đã dùng hết lượt chat hôm nay. Vui lòng quay lại vào ngày mai.",
        )
