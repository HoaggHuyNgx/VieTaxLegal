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
    ) -> None:
        self._max_failures = max_failures
        self._window_seconds = window_seconds
        self._clock = clock
        self._failures: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def _recent(self, key: str, now: float) -> list[float]:
        cutoff = now - self._window_seconds
        recent = [stamp for stamp in self._failures.get(key, []) if stamp > cutoff]
        if recent:
            self._failures[key] = recent
        else:
            self._failures.pop(key, None)
        return recent

    def check(self, key: str) -> None:
        with self._lock:
            if len(self._recent(key, self._clock())) >= self._max_failures:
                raise AppError(
                    429,
                    "AUTH_RATE_LIMITED",
                    "Bạn đã nhập sai quá nhiều lần. Vui lòng thử lại sau ít phút.",
                )

    def record_failure(self, key: str) -> None:
        with self._lock:
            now = self._clock()
            recent = self._recent(key, now)
            if key not in self._failures and len(self._failures) >= MAX_TRACKED_KEYS:
                self._failures.pop(next(iter(self._failures)))
            self._failures[key] = [*recent, now]

    def reset(self, key: str) -> None:
        with self._lock:
            self._failures.pop(key, None)


@lru_cache
def get_login_throttle() -> LoginThrottle:
    settings = get_settings()
    return LoginThrottle(
        settings.login_max_failed_attempts,
        settings.login_attempt_window_minutes * 60,
    )
