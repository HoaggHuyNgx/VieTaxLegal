import pytest
from fastapi.testclient import TestClient

from app.core.errors import AppError
from app.services import login_throttle
from app.services.login_throttle import LoginThrottle

PASSWORD = "mat-khau-an-toan"


class FakeClock:
    def __init__(self) -> None:
        self.now = 1_000.0

    def __call__(self) -> float:
        return self.now


def make_throttle(clock: FakeClock, max_failures: int = 3) -> LoginThrottle:
    return LoginThrottle(max_failures, window_seconds=60, clock=clock)


def test_locks_after_max_failures_and_unlocks_when_window_passes() -> None:
    clock = FakeClock()
    throttle = make_throttle(clock)
    for _ in range(3):
        throttle.check("key")
        throttle.record_failure("key")

    with pytest.raises(AppError) as locked:
        throttle.check("key")
    assert locked.value.status_code == 429
    assert locked.value.code == "AUTH_RATE_LIMITED"

    clock.now += 61
    throttle.check("key")


def test_failures_expire_individually() -> None:
    clock = FakeClock()
    throttle = make_throttle(clock)
    throttle.record_failure("key")
    clock.now += 40
    throttle.record_failure("key")
    throttle.record_failure("key")
    with pytest.raises(AppError):
        throttle.check("key")

    clock.now += 30  # the first failure is now 70s old and drops out of the window
    throttle.check("key")


def test_reset_and_other_keys_are_independent() -> None:
    throttle = make_throttle(FakeClock())
    for _ in range(3):
        throttle.record_failure("a")

    throttle.check("b")
    throttle.reset("a")
    throttle.check("a")


def test_tracked_keys_are_capped(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(login_throttle, "MAX_TRACKED_KEYS", 2)
    throttle = make_throttle(FakeClock())
    for key in ("a", "b", "c"):
        throttle.record_failure(key)

    assert list(throttle._failures) == ["b", "c"]


def register(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "email": "throttle@example.com",
            "username": "throttle_user",
            "fullName": "Throttle Tester",
            "password": PASSWORD,
            "acceptTerms": True,
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
