from fastapi.testclient import TestClient
from sqlalchemy import select

from app.models.user import User


def register_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "email": "huy@example.com",
        "username": "huy_legal",
        "fullName": "Hoàng Huy",
        "phone": "0901 234 567",
        "password": "mat-khau-an-toan",
        "acceptTerms": True,
    }
    payload.update(overrides)
    return payload


def create_user(client: TestClient, **overrides: object) -> None:
    response = client.post("/api/auth/register", json=register_payload(**overrides))
    assert response.status_code == 201


def test_health_reports_database_connection(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_register_creates_normalized_user_and_session(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json=register_payload(email="HUY@EXAMPLE.COM", username="HUY_LEGAL"),
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": response.json()["id"],
        "email": "huy@example.com",
        "username": "huy_legal",
        "fullName": "Hoàng Huy",
        "phone": "0901234567",
    }
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    assert "max-age" not in cookie

    me_response = client.get("/api/auth/me")
    assert me_response.status_code == 200
    assert me_response.json()["username"] == "huy_legal"


def test_register_rejects_duplicate_email_and_username(client: TestClient) -> None:
    create_user(client)

    duplicate_email = client.post(
        "/api/auth/register",
        json=register_payload(username="another_user"),
    )
    duplicate_username = client.post(
        "/api/auth/register",
        json=register_payload(email="another@example.com"),
    )

    assert duplicate_email.status_code == 409
    assert duplicate_email.json()["error"]["code"] == "EMAIL_TAKEN"
    assert duplicate_email.json()["error"]["fields"] == {"email": "Email đã tồn tại."}
    assert duplicate_username.status_code == 409
    assert duplicate_username.json()["error"]["code"] == "USERNAME_TAKEN"
    assert duplicate_username.json()["error"]["fields"] == {"username": "Tên tài khoản đã tồn tại."}


def test_register_rejects_invalid_phone(client: TestClient) -> None:
    response = client.post("/api/auth/register", json=register_payload(phone="not-a-phone"))

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "phone" in response.json()["error"]["fields"]


def test_login_accepts_email_and_username(client: TestClient) -> None:
    create_user(client)
    client.cookies.clear()

    email_login = client.post(
        "/api/auth/login",
        json={"identifier": "HUY@EXAMPLE.COM", "password": "mat-khau-an-toan", "rememberMe": False},
    )
    assert email_login.status_code == 200
    assert email_login.json()["email"] == "huy@example.com"

    client.cookies.clear()
    username_login = client.post(
        "/api/auth/login",
        json={"identifier": "HUY_LEGAL", "password": "mat-khau-an-toan", "rememberMe": False},
    )
    assert username_login.status_code == 200
    assert username_login.json()["username"] == "huy_legal"


def test_login_rejects_invalid_password(client: TestClient) -> None:
    create_user(client)
    client.cookies.clear()

    response = client.post(
        "/api/auth/login",
        json={"identifier": "huy_legal", "password": "sai-mat-khau", "rememberMe": False},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_login_rejects_inactive_user(client: TestClient, database_session) -> None:
    create_user(client)
    user = database_session.scalar(select(User).where(User.username == "huy_legal"))
    assert user is not None
    user.is_active = False
    database_session.commit()
    client.cookies.clear()

    response = client.post(
        "/api/auth/login",
        json={"identifier": "huy_legal", "password": "mat-khau-an-toan", "rememberMe": False},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_me_requires_session_and_logout_clears_it(client: TestClient) -> None:
    assert client.get("/api/auth/me").status_code == 401

    create_user(client)
    assert client.get("/api/auth/me").status_code == 200

    logout_response = client.post("/api/auth/logout")
    assert logout_response.status_code == 204
    assert "max-age=0" in logout_response.headers["set-cookie"].lower()
    assert client.get("/api/auth/me").status_code == 401


def test_me_rejects_invalid_or_inactive_session(client: TestClient, database_session) -> None:
    client.cookies.set("vietaxlegal_session", "not-a-valid-session")
    assert client.get("/api/auth/me").status_code == 401

    client.cookies.clear()
    create_user(client)
    user = database_session.scalar(select(User).where(User.username == "huy_legal"))
    assert user is not None
    user.is_active = False
    database_session.commit()

    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


def test_remember_me_sets_persistent_cookie(client: TestClient) -> None:
    create_user(client)
    client.cookies.clear()

    response = client.post(
        "/api/auth/login",
        json={"identifier": "huy_legal", "password": "mat-khau-an-toan", "rememberMe": True},
    )

    assert response.status_code == 200
    assert "max-age=2592000" in response.headers["set-cookie"].lower()
