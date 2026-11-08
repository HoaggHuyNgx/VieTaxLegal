import re
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import create_session_token
from app.models.email_otp import EmailOtp
from app.services import mailer
from app.services.email_otp import MAX_ATTEMPTS, create_email_proof
from tests.test_auth import create_user, register_payload

EMAIL = "nguoi.moi@example.com"


@pytest.fixture
def outbox(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, str, str]]:
    """Capture mail instead of sending it: tests never talk to an SMTP server."""
    sent: list[tuple[str, str, str]] = []
    monkeypatch.setattr(
        mailer, "send_mail", lambda to, subject, body: sent.append((to, subject, body))
    )
    return sent


def last_code(outbox: list[tuple[str, str, str]]) -> str:
    match = re.search(r"\b(\d{6})\b", outbox[-1][2])
    assert match
    return match.group(1)


def request_code(client: TestClient, email: str = EMAIL):
    return client.post("/api/auth/email-code", json={"email": email})


def verify(client: TestClient, code: str, email: str = EMAIL):
    return client.post("/api/auth/email-code/verify", json={"email": email, "code": code})


def age_codes(database_session, by: timedelta) -> None:
    """Make every stored code look `by` older (to step past the cooldown or the expiry)."""
    for row in database_session.scalars(select(EmailOtp)):
        row.created_at -= by
        row.expires_at -= by
    database_session.commit()


def test_code_is_mailed_and_stored_only_as_a_hash(client, outbox, database_session) -> None:
    response = request_code(client)

    assert response.status_code == 204
    assert outbox[0][0] == EMAIL
    code = last_code(outbox)
    assert database_session.scalar(select(EmailOtp)).code_hash != code


def test_correct_code_yields_a_proof_that_allows_registration(client, outbox) -> None:
    request_code(client)

    proof = verify(client, last_code(outbox)).json()["proof"]
    response = client.post(
        "/api/auth/register", json=register_payload(email=EMAIL, emailProof=proof)
    )

    assert response.status_code == 201


def test_wrong_code_is_rejected_and_counts_an_attempt(client, outbox, database_session) -> None:
    request_code(client)
    wrong = "000000" if last_code(outbox) != "000000" else "111111"

    response = verify(client, wrong)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "OTP_INVALID"
    assert database_session.scalar(select(EmailOtp)).attempts == 1


def test_too_many_wrong_codes_burn_the_code_even_for_the_right_one(client, outbox) -> None:
    request_code(client)
    right = last_code(outbox)
    wrong = "000000" if right != "000000" else "111111"
    for _ in range(MAX_ATTEMPTS):
        verify(client, wrong)

    response = verify(client, right)

    assert response.status_code == 429
    assert response.json()["error"]["code"] == "OTP_TOO_MANY_ATTEMPTS"


def test_an_expired_code_is_rejected(client, outbox, database_session) -> None:
    request_code(client)
    age_codes(database_session, timedelta(minutes=11))

    response = verify(client, last_code(outbox))

    assert response.json()["error"]["code"] == "OTP_EXPIRED"


def test_a_code_works_only_once(client, outbox) -> None:
    request_code(client)
    code = last_code(outbox)
    assert verify(client, code).status_code == 200

    assert verify(client, code).json()["error"]["code"] == "OTP_INVALID"


def test_resend_is_blocked_during_the_cooldown_then_allowed(
    client, outbox, database_session
) -> None:
    request_code(client)

    blocked = request_code(client)
    age_codes(database_session, timedelta(seconds=61))
    allowed = request_code(client)

    assert blocked.json()["error"]["code"] == "OTP_RATE_LIMITED"
    assert allowed.status_code == 204
    assert len(outbox) == 2


def test_at_most_five_codes_per_hour_per_email(client, outbox, database_session) -> None:
    for _ in range(5):
        assert request_code(client).status_code == 204
        age_codes(database_session, timedelta(seconds=61))

    response = request_code(client)

    assert response.json()["error"]["code"] == "OTP_RATE_LIMITED"


def test_an_already_registered_email_gets_no_mail(client, outbox) -> None:
    create_user(client)

    response = request_code(client, "huy@example.com")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EMAIL_TAKEN"
    assert outbox == []


def test_a_failed_send_does_not_start_the_cooldown(client, monkeypatch, database_session) -> None:
    def fail(*_: object) -> None:
        raise AppError(502, "EMAIL_SEND_FAILED", "x")

    monkeypatch.setattr(mailer, "send_mail", fail)
    failed = request_code(client)
    sent: list[str] = []
    monkeypatch.setattr(mailer, "send_mail", lambda to, subject, body: sent.append(to))

    retry = request_code(client)

    assert failed.json()["error"]["code"] == "EMAIL_SEND_FAILED"
    assert retry.status_code == 204 and sent == [EMAIL]
    assert database_session.scalar(select(func.count()).select_from(EmailOtp)) == 1


def test_without_smtp_settings_registration_codes_are_unavailable(client, database_session) -> None:
    response = request_code(client)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "EMAIL_NOT_CONFIGURED"
    assert database_session.scalar(select(func.count()).select_from(EmailOtp)) == 0


def test_one_client_cannot_request_unlimited_codes(client, outbox) -> None:
    for index in range(10):
        assert request_code(client, f"user{index}@example.com").status_code == 204

    response = request_code(client, "user10@example.com")

    assert response.status_code == 429
    assert response.json()["error"]["code"] == "OTP_RATE_LIMITED"


def test_registration_requires_a_proof_for_that_exact_email(client) -> None:
    missing = register_payload(email=EMAIL)
    del missing["emailProof"]

    no_proof = client.post("/api/auth/register", json=missing)
    other_email = client.post(
        "/api/auth/register",
        json=register_payload(
            email=EMAIL, emailProof=create_email_proof("someone.else@example.com")
        ),
    )
    garbage = client.post(
        "/api/auth/register", json=register_payload(email=EMAIL, emailProof="not-a-token")
    )

    assert no_proof.status_code == 422
    for response in (other_email, garbage):
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "EMAIL_NOT_VERIFIED"


def test_an_access_token_or_expired_proof_is_not_a_valid_proof(client) -> None:
    settings = get_settings()
    expired = jwt.encode(
        {
            "type": "email_proof",
            "email": EMAIL,
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )
    access_token = create_session_token(uuid4())

    for proof in (expired, access_token):
        response = client.post(
            "/api/auth/register", json=register_payload(email=EMAIL, emailProof=proof)
        )
        assert response.json()["error"]["code"] == "EMAIL_NOT_VERIFIED"


def test_a_racing_request_that_committed_first_blocks_this_one(
    client, outbox, database_session
) -> None:
    """Simulate a parallel request whose row landed just before ours."""
    now = datetime.now(timezone.utc)
    database_session.add(
        EmailOtp(
            email=EMAIL, code_hash="x" * 64, expires_at=now + timedelta(minutes=10), created_at=now
        )
    )
    database_session.commit()

    response = request_code(client)

    assert response.json()["error"]["code"] == "OTP_RATE_LIMITED"
    assert outbox == []
    assert database_session.scalar(select(func.count()).select_from(EmailOtp)) == 1
