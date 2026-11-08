import threading

import pytest
from fastapi.testclient import TestClient

from app.core.errors import AppError
from app.services import login_throttle
from app.services.login_throttle import LoginThrottle
from tests.test_auth import email_proof

PASSWORD = "Mat-khau-an-toan-2026!"


class FakeClock:
    def __init__(self) -> None:
        self.now = 1_000.0

    def __call__(self) -> float:
        return self.now


def make_throttle(clock: FakeClock, max_failures: int = 3) -> LoginThrottle:
    return LoginThrottle(max_failures, window_seconds=60, clock=clock)


def attempt(throttle: LoginThrottle, key: str = "key") -> None:
    throttle.acquire(key)


def test_locks_after_max_attempts_and_unlocks_when_window_passes() -> None:
    clock = FakeClock()
    throttle = make_throttle(clock)
    for _ in range(3):
        attempt(throttle)

    with pytest.raises(AppError) as locked:
        attempt(throttle)
    assert locked.value.status_code == 429
    assert locked.value.code == "AUTH_RATE_LIMITED"

    clock.now += 61
    attempt(throttle)


def test_attempts_expire_individually() -> None:
    clock = FakeClock()
    throttle = make_throttle(clock)
    attempt(throttle)
    clock.now += 40
    attempt(throttle)
    attempt(throttle)
    with pytest.raises(AppError):
        attempt(throttle)

    clock.now += 30  # the first attempt is now 70s old and drops out of the window
    attempt(throttle)


def test_blocked_attempts_do_not_extend_the_lock() -> None:
    clock = FakeClock()
    throttle = make_throttle(clock)
    for _ in range(3):
        attempt(throttle)
    clock.now += 30
    with pytest.raises(AppError):
        attempt(throttle)

    clock.now += 31  # 61s after the real attempts, only 31s after the blocked one
    attempt(throttle)


def test_reset_and_other_keys_are_independent() -> None:
    throttle = make_throttle(FakeClock())
    for _ in range(3):
        attempt(throttle, "a")

    attempt(throttle, "b")
    throttle.reset("a")
    attempt(throttle, "a")


def test_parallel_attempts_cannot_exceed_the_limit() -> None:
    throttle = make_throttle(FakeClock(), max_failures=5)
    allowed = 0
    lock = threading.Lock()

    def worker() -> None:
        nonlocal allowed
        try:
            throttle.acquire("key")
        except AppError:
            return
        with lock:
            allowed += 1

    threads = [threading.Thread(target=worker) for _ in range(50)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert allowed == 5


def test_full_table_evicts_least_recently_used_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(login_throttle, "MAX_TRACKED_KEYS", 2)
    throttle = make_throttle(FakeClock(), max_failures=2)
    attempt(throttle, "target")
    attempt(throttle, "other")
    attempt(throttle, "target")  # target is now the most recently used

    attempt(throttle, "flood")  # evicts "other", not "target"

    assert set(throttle._failures) == {"target", "flood"}
    with pytest.raises(AppError):
        attempt(throttle, "target")  # its count survived the flood


def register(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "email": "throttle@example.com",
            "username": "throttle_user",
            "fullName": "Throttle Tester",
            "password": PASSWORD,
            "acceptTerms": True,
            "emailProof": email_proof("throttle@example.com"),
        },
    )
    assert response.status_code == 201
    client.post("/api/auth/logout")


def login(client: TestClient, identifier: str, password: str) -> object:
    return client.post(
        "/api/auth/login",
        json={"identifier": identifier, "password": password, "rememberMe": False},
    )


def test_login_locks_after_repeated_failures_even_with_correct_password(
    client: TestClient,
) -> None:
    register(client)
    for _ in range(5):
        assert login(client, "throttle@example.com", "sai-mat-khau").status_code == 401

    blocked = login(client, "throttle@example.com", PASSWORD)

    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "AUTH_RATE_LIMITED"
    assert "set-cookie" not in blocked.headers


def test_successful_login_clears_failure_count(client: TestClient) -> None:
    register(client)
    for _ in range(4):
        assert login(client, "throttle@example.com", "sai-mat-khau").status_code == 401
    assert login(client, "throttle@example.com", PASSWORD).status_code == 200

    for _ in range(4):
        assert login(client, "throttle@example.com", "sai-mat-khau").status_code == 401


def test_other_identifier_is_not_locked(client: TestClient) -> None:
    register(client)
    for _ in range(5):
        login(client, "throttle@example.com", "sai-mat-khau")

    assert login(client, "throttle_user", PASSWORD).status_code == 200


def test_unknown_account_is_throttled_like_a_known_one(client: TestClient) -> None:
    for _ in range(5):
        assert login(client, "nobody@example.com", "sai-mat-khau").status_code == 401

    blocked = login(client, "nobody@example.com", "sai-mat-khau")

    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "AUTH_RATE_LIMITED"
