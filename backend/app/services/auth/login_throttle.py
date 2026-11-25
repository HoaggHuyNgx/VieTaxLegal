import threading
import time
from collections.abc import Callable
from functools import lru_cache

from app.core.config import get_settings
from app.core.errors import AppError

# Hard cap so a flood of distinct identifiers cannot grow the table without bound.
MAX_TRACKED_KEYS = 10_000


class LoginThrottle:
    """Sliding-window counter of failed logins, kept in process memory.

    State resets on restart and is not shared between workers; that is acceptable for a
    single-process deployment and avoids a table plus migration.
    """

    def __init__(
        self,
        max_failures: int,
        window_seconds: float,
        clock: Callable[[], float] = time.monotonic,
        error_code: str = "AUTH_RATE_LIMITED",
        error_message: str = "Bạn đã nhập sai quá nhiều lần. Vui lòng thử lại sau ít phút.",
    ) -> None:
        self._error_code = error_code
        self._error_message = error_message
        self._max_failures = max_failures
        self._window_seconds = window_seconds
        self._clock = clock
        self._failures: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def _recent(self, key: str, now: float) -> list[float]:
        cutoff = now - self._window_seconds
        recent = [stamp for stamp in self._failures.pop(key, []) if stamp > cutoff]
        if recent:
            self._failures[key] = recent  # re-inserted last: dict order doubles as LRU order
        return recent

    def acquire(self, key: str) -> None:
        """Count this attempt, or raise 429 if the key is already at its limit.

        Check and count happen under one lock, so a burst of parallel requests cannot all
        pass the check before any of them is recorded. Callers `reset` on success.
        """
        with self._lock:
            now = self._clock()
            recent = self._recent(key, now)
            if len(recent) >= self._max_failures:
                self._failures[key] = recent
                raise AppError(429, self._error_code, self._error_message)
            if not recent and len(self._failures) >= MAX_TRACKED_KEYS:
                # Evict the least recently used key, so an active attacker's own key
                # survives while idle ones go.
                self._failures.pop(next(iter(self._failures)))
            self._failures[key] = [*recent, now]

    def reset(self, key: str) -> None:
        with self._lock:
            self._failures.pop(key, None)


@lru_cache
def get_register_throttle() -> LoginThrottle:
    """Counts every registration attempt per client address (not only failures)."""
    return LoginThrottle(
        get_settings().register_max_per_hour,
        3600,
        error_code="REGISTER_RATE_LIMITED",
        error_message="Bạn đã tạo tài khoản quá nhiều lần. Vui lòng thử lại sau.",
    )


@lru_cache
def get_email_code_throttle() -> LoginThrottle:
    """Counts every code request per client address, so the form cannot be used to mail-bomb."""
    return LoginThrottle(
        get_settings().register_max_per_hour,
        3600,
        error_code="OTP_RATE_LIMITED",
        error_message="Bạn yêu cầu mã quá nhiều lần. Vui lòng thử lại sau.",
    )


@lru_cache
def get_login_throttle() -> LoginThrottle:
    settings = get_settings()
    return LoginThrottle(
        settings.login_max_failed_attempts,
        settings.login_attempt_window_minutes * 60,
    )
