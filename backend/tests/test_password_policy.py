from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.models.user import User
from app.services.password_policy import failed_rules
from tests.test_auth import register_payload

GOOD = "Mat-khau-an-toan-2026!"


@pytest.mark.parametrize(
    ("password", "expected"),
    [
        (GOOD, []),
        ("Ngay nay troi dep 2026?", []),  # spaces are fine, and the special character is "?"
        ("Cà-phê-sữa-đá-2026", []),  # Vietnamese letters are letters
        ("Ab1!", ["length"]),
        ("mat-khau-an-toan-2026!", ["upper"]),
        ("Mat-khau-an-toan-abc!", ["digit"]),
        ("Matkhauantoan2026ab", ["special"]),
        ("matkhau", ["length", "upper", "digit", "special"]),
        ("Pass 1234 5678 word", ["special"]),  # a space alone is not a special character
    ],
)
def test_failed_rules(password: str, expected: list[str]) -> None:
    assert failed_rules(password) == expected


def test_password_may_not_contain_the_email_name_or_the_username() -> None:
    assert failed_rules("Xin-chao-Huy-2026!", "huy@example.com", "ten_khac") == ["identity"]
    assert failed_rules("Xin-chao-HUY_LEGAL-2026!", "a@b.com", "huy_legal") == ["identity"]
    assert failed_rules("Xin-chao-gia.huy-2026!", "gia.huy@example.com", "x_y_z") == ["identity"]


def test_very_short_identity_parts_do_not_block_everything() -> None:
    assert failed_rules("Xin-chao-bay-gio-2026!", "a@b.com", "ab") == []


def register(client: TestClient, password: str, **overrides: object):
    return client.post("/api/auth/register", json=register_payload(password=password, **overrides))


def test_register_accepts_a_compliant_password(client: TestClient) -> None:
    assert register(client, GOOD).status_code == 201


@pytest.mark.parametrize(
    ("password", "message_part"),
    [
        ("Ab1!", "ít nhất 12 ký tự"),
        ("mat-khau-an-toan-2026!", "một chữ hoa"),
        ("Mat-khau-an-toan-abc!", "một chữ số"),
        ("Matkhauantoan2026ab", "một ký tự đặc biệt"),
    ],
)
def test_register_rejects_a_weak_password_and_says_why(
    client: TestClient, password: str, message_part: str
) -> None:
    response = register(client, password)

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert message_part in error["fields"]["password"]
    assert not error["fields"]["password"].startswith("Value error")


def test_register_lists_every_missing_rule_at_once(client: TestClient) -> None:
    message = register(client, "matkhau").json()["error"]["fields"]["password"]

    for part in ("12 ký tự", "chữ hoa", "chữ số", "ký tự đặc biệt"):
        assert part in message


def test_register_rejects_a_password_containing_the_username_or_email(client: TestClient) -> None:
    response = register(client, "Xin-chao-huy_legal-2026!", username="huy_legal")
    by_email = register(client, "Xin-chao-nguoi.dung-2026!", email="nguoi.dung@example.com")

    for rejected in (response, by_email):
        assert rejected.status_code == 422
        assert "email hoặc tên tài khoản" in rejected.json()["error"]["fields"]["password"]


def test_password_length_is_capped_at_128(client: TestClient) -> None:
    longest = "Aa1!" + "x" * 124
    too_long = longest + "x"

    assert register(client, longest).status_code == 201
    assert register(client, too_long, email="khac@example.com", username="khac").status_code == 422


def test_existing_users_with_old_short_passwords_can_still_log_in(
    client: TestClient, database_session
) -> None:
    database_session.add(
        User(
            email="cu@example.com",
            username="nguoi_cu",
            full_name="Người Cũ",
            password_hash=hash_password("matkhau8"),  # 8 chars, no upper/digit/special
            terms_accepted_at=datetime.now(timezone.utc),
        )
    )
    database_session.commit()

    response = client.post(
        "/api/auth/login", json={"identifier": "nguoi_cu", "password": "matkhau8"}
    )

    assert response.status_code == 200
