import time
from collections.abc import Generator
from urllib.parse import parse_qs, urlparse

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core.config import get_settings
from app.models.oauth_identity import OAuthIdentity
from app.models.user import User
from app.services import google_oauth
from tests.test_auth import create_user

CLIENT_ID = "test-client-id"
FRONTEND = "http://localhost:3000"


@pytest.fixture
def google_enabled(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    monkeypatch.setenv("GOOGLE_CLIENT_ID", CLIENT_ID)
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test-client-secret")
    get_settings.cache_clear()
    yield
    monkeypatch.undo()
    get_settings.cache_clear()


def start(client: TestClient, path: str = "/api/auth/google/login") -> tuple[str, str]:
    response = client.get(path, follow_redirects=False)
    assert response.status_code == 302
    query = parse_qs(urlparse(response.headers["location"]).query)
    return query["state"][0], query["nonce"][0]


def finish(client: TestClient, monkeypatch, state: str, issued_nonce: str, **claims):
    """Play Google's side: hand the callback an ID token carrying `claims`."""
    token = jwt.encode(
        {
            "iss": "https://accounts.google.com",
            "aud": CLIENT_ID,
            "exp": int(time.time()) + 300,
            "nonce": issued_nonce,
            "sub": "google-sub-1",
            "email": "gia.huy@example.com",
            "email_verified": True,
            "name": "Gia Huy",
            **claims,
        },
        "an-unchecked-key-of-sufficient-length-1234",
        algorithm="HS256",
    )
    monkeypatch.setattr(google_oauth, "exchange_code", lambda code, flow: token)
    return client.get(
        "/api/auth/google/callback", params={"code": "c", "state": state}, follow_redirects=False
    )


def sign_in(client: TestClient, monkeypatch, **claims):
    state, nonce = start(client)
    return finish(client, monkeypatch, state, nonce, **claims)


def user_count(database_session) -> int:
    return database_session.scalar(select(func.count()).select_from(User))


def test_google_login_is_off_until_configured(client: TestClient) -> None:
    response = client.get("/api/auth/google/login", follow_redirects=False)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "GOOGLE_NOT_CONFIGURED"


def test_login_redirects_to_google_with_pkce_and_state_cookie(
    client: TestClient, google_enabled: None
) -> None:
    response = client.get("/api/auth/google/login", follow_redirects=False)

    query = parse_qs(urlparse(response.headers["location"]).query)
    assert response.headers["location"].startswith("https://accounts.google.com/")
    assert query["client_id"] == [CLIENT_ID]
    assert query["code_challenge_method"] == ["S256"]
    assert query["scope"] == ["openid email profile"]
    assert "httponly" in response.headers["set-cookie"].lower()


def test_new_google_user_is_created_and_signed_in(
    client: TestClient, google_enabled: None, monkeypatch, database_session
) -> None:
    response = sign_in(client, monkeypatch)

    assert response.headers["location"] == f"{FRONTEND}/chat"
    me = client.get("/api/auth/me").json()
    assert me["email"] == "gia.huy@example.com"
    assert me["username"] == "gia_huy"
    assert me["hasPassword"] is False
    assert me["googleLinked"] is True
    assert database_session.scalar(select(User)).password_hash is None


def test_known_google_account_signs_in_even_if_its_email_changed(
    client: TestClient, google_enabled: None, monkeypatch, database_session
) -> None:
    sign_in(client, monkeypatch)
    client.cookies.clear()

    response = sign_in(client, monkeypatch, email="renamed@example.com")

    assert response.headers["location"] == f"{FRONTEND}/chat"
    assert user_count(database_session) == 1
    assert client.get("/api/auth/me").json()["email"] == "gia.huy@example.com"


def test_email_of_a_password_account_is_not_linked_automatically(
    client: TestClient, google_enabled: None, monkeypatch, database_session
) -> None:
    create_user(client, email="gia.huy@example.com")
    client.cookies.clear()

    response = sign_in(client, monkeypatch)

    assert (
        response.headers["location"] == f"{FRONTEND}/?authError=GOOGLE_EMAIL_NEEDS_PASSWORD_LOGIN"
    )
    assert client.get("/api/auth/me").status_code == 401
    assert database_session.scalar(select(func.count()).select_from(OAuthIdentity)) == 0


def test_signed_in_user_can_link_google_then_use_it_to_log_in(
    client: TestClient, google_enabled: None, monkeypatch
) -> None:
    create_user(client)
    state, nonce = start(client, "/api/auth/google/link")

    response = finish(client, monkeypatch, state, nonce, email="other@example.com")

    assert response.headers["location"] == f"{FRONTEND}/settings?google=linked"
    assert client.get("/api/auth/me").json()["googleLinked"] is True
    client.cookies.clear()
    sign_in(client, monkeypatch, email="other@example.com")
    assert client.get("/api/auth/me").json()["username"] == "huy_legal"


def test_link_requires_a_session(client: TestClient, google_enabled: None) -> None:
    response = client.get("/api/auth/google/link", follow_redirects=False)

    assert response.status_code == 401


def test_link_refuses_a_google_account_used_by_someone_else(
    client: TestClient, google_enabled: None, monkeypatch
) -> None:
    sign_in(client, monkeypatch)  # google-sub-1 now belongs to a Google-created user
    client.cookies.clear()
    create_user(client)
    state, nonce = start(client, "/api/auth/google/link")

    response = finish(client, monkeypatch, state, nonce)

    assert response.headers["location"] == f"{FRONTEND}/settings?authError=GOOGLE_ACCOUNT_TAKEN"


def test_link_twice_is_refused(client: TestClient, google_enabled: None, monkeypatch) -> None:
    create_user(client)
    finish(client, monkeypatch, *start(client, "/api/auth/google/link"))

    response = finish(client, monkeypatch, *start(client, "/api/auth/google/link"), sub="another")

    assert response.headers["location"] == f"{FRONTEND}/settings?authError=GOOGLE_ALREADY_LINKED"


@pytest.mark.parametrize(
    "bad_claims",
    [
        {"nonce": "not-the-nonce"},
        {"aud": "someone-elses-client"},
        {"iss": "https://evil.example.com"},
        {"exp": 1},
        {"email_verified": False},
        {"sub": ""},
    ],
)
def test_invalid_id_token_claims_are_rejected(
    client: TestClient, google_enabled: None, monkeypatch, database_session, bad_claims
) -> None:
    response = sign_in(client, monkeypatch, **bad_claims)

    assert response.headers["location"] == f"{FRONTEND}/?authError=GOOGLE_AUTH_FAILED"
    assert user_count(database_session) == 0


def test_callback_with_wrong_state_or_without_cookie_fails(
    client: TestClient, google_enabled: None, monkeypatch
) -> None:
    _, nonce = start(client)
    wrong_state = finish(client, monkeypatch, "forged-state", nonce)
    client.cookies.clear()
    no_cookie = finish(client, monkeypatch, "anything", nonce)

    for response in (wrong_state, no_cookie):
        assert response.headers["location"] == f"{FRONTEND}/?authError=GOOGLE_AUTH_FAILED"


def test_user_cancelling_on_google_returns_a_failure(
    client: TestClient, google_enabled: None
) -> None:
    start(client)

    response = client.get(
        "/api/auth/google/callback", params={"error": "access_denied"}, follow_redirects=False
    )

    assert response.headers["location"] == f"{FRONTEND}/?authError=GOOGLE_AUTH_FAILED"


def test_deactivated_google_user_cannot_sign_in(
    client: TestClient, google_enabled: None, monkeypatch, database_session
) -> None:
    sign_in(client, monkeypatch)
    client.cookies.clear()
    database_session.scalar(select(User)).is_active = False
    database_session.commit()

    response = sign_in(client, monkeypatch)

    assert response.headers["location"] == f"{FRONTEND}/?authError=GOOGLE_AUTH_FAILED"
    assert client.get("/api/auth/me").status_code == 401


def test_google_only_account_cannot_use_password_login(
    client: TestClient, google_enabled: None, monkeypatch
) -> None:
    sign_in(client, monkeypatch)
    client.cookies.clear()

    response = client.post(
        "/api/auth/login", json={"identifier": "gia.huy@example.com", "password": "any-password-1"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_generated_username_avoids_collisions(
    client: TestClient, google_enabled: None, monkeypatch, database_session
) -> None:
    create_user(client, username="gia_huy", email="taken@example.com")
    client.cookies.clear()

    sign_in(client, monkeypatch)

    names = {user.username for user in database_session.scalars(select(User))}
    assert "gia_huy" in names and len(names) == 2


def test_state_cookie_is_not_accepted_as_a_session(
    client: TestClient, google_enabled: None
) -> None:
    response = client.get("/api/auth/google/login", follow_redirects=False)
    state_cookie = response.cookies.get("vietaxlegal_google_state")
    client.cookies.clear()
    client.cookies.set("vietaxlegal_session", state_cookie)

    assert client.get("/api/auth/me").status_code == 401


def test_full_name_falls_back_to_the_email_when_too_short(
    client: TestClient, google_enabled: None, monkeypatch, database_session
) -> None:
    sign_in(client, monkeypatch, email="a@example.com", name=None)

    assert database_session.scalar(select(User)).full_name == "a@example.com"
