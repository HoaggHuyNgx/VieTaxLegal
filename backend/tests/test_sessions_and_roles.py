from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.models.refresh_token import RefreshToken
from app.models.user import ROLE_ADMIN, User
from tests.test_auth import create_user, register_payload

PASSWORD = "mat-khau-an-toan"


def refresh_cookie(client: TestClient) -> str:
    return client.cookies.get("vietaxlegal_refresh")


def test_refresh_rotates_token_and_reissues_access(client: TestClient) -> None:
    create_user(client)
    first = refresh_cookie(client)
    client.cookies.delete("vietaxlegal_session")  # access JWT "expired"
    assert client.get("/api/auth/me").status_code == 401

    response = client.post("/api/auth/refresh")

    assert response.status_code == 200
    assert refresh_cookie(client) != first
    assert client.get("/api/auth/me").status_code == 200


def test_reusing_old_refresh_token_revokes_the_whole_family(
    client: TestClient, database_session
) -> None:
    create_user(client)
    stolen = refresh_cookie(client)
    assert client.post("/api/auth/refresh").status_code == 200
    # Replay of a rotated token, after the race-tolerance window.
    row = database_session.scalars(select(RefreshToken).order_by(RefreshToken.created_at)).first()
    row.revoked_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    database_session.commit()

    client.cookies.set("vietaxlegal_refresh", stolen, path="/api/auth")
    assert client.post("/api/auth/refresh").status_code == 401

    live = database_session.scalars(
        select(RefreshToken).where(RefreshToken.revoked_at.is_(None))
    ).all()
    assert live == []


def test_refresh_without_cookie_is_401(client: TestClient) -> None:
    response = client.post("/api/auth/refresh")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


def test_expired_refresh_token_is_rejected(client: TestClient, database_session) -> None:
    create_user(client)
    row = database_session.scalars(select(RefreshToken)).one()
    row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    database_session.commit()

    assert client.post("/api/auth/refresh").status_code == 401


def test_logout_revokes_refresh_token_server_side(client: TestClient) -> None:
    create_user(client)
    token = refresh_cookie(client)

    assert client.post("/api/auth/logout").status_code == 204

    client.cookies.set("vietaxlegal_refresh", token, path="/api/auth")
    assert client.post("/api/auth/refresh").status_code == 401


def test_deactivated_user_cannot_refresh(client: TestClient, database_session) -> None:
    create_user(client)
    user = database_session.scalar(select(User))
    user.is_active = False
    database_session.commit()

    assert client.post("/api/auth/refresh").status_code == 401


def promote(database_session, username: str) -> None:
    user = database_session.scalar(select(User).where(User.username == username))
    user.role = ROLE_ADMIN
    database_session.commit()


def test_admin_endpoints_require_admin_role(client: TestClient, database_session) -> None:
    assert client.get("/api/admin/users").status_code == 401

    create_user(client)
    forbidden = client.get("/api/admin/users")
    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "FORBIDDEN"

    promote(database_session, "huy_legal")
    allowed = client.get("/api/admin/users")
    assert allowed.status_code == 200
    assert allowed.json()[0]["role"] == "admin"


def test_admin_can_deactivate_user_and_revoke_their_sessions(
    client: TestClient, database_session
) -> None:
    create_user(client, email="victim@example.com", username="victim")
    victim_id = client.get("/api/auth/me").json()["id"]
    victim_refresh = refresh_cookie(client)
    client.cookies.clear()
    create_user(client)
    promote(database_session, "huy_legal")

    response = client.patch(f"/api/admin/users/{victim_id}", json={"isActive": False})

    assert response.status_code == 200
    assert response.json()["isActive"] is False
    client.cookies.clear()
    client.cookies.set("vietaxlegal_refresh", victim_refresh, path="/api/auth")
    assert client.post("/api/auth/refresh").status_code == 401


def test_admin_cannot_modify_self_or_set_unknown_role(client: TestClient, database_session) -> None:
    create_user(client)
    promote(database_session, "huy_legal")
    me = client.get("/api/auth/me").json()

    own = client.patch(f"/api/admin/users/{me['id']}", json={"isActive": False})
    assert own.status_code == 409

    client.cookies.clear()
    create_user(client, email="b@example.com", username="user_b")
    other = client.get("/api/auth/me").json()["id"]
    client.cookies.clear()
    client.post("/api/auth/login", json={"identifier": "huy_legal", "password": PASSWORD})
    assert client.patch(f"/api/admin/users/{other}", json={"role": "root"}).status_code == 422


def test_register_is_rate_limited_per_client(client: TestClient) -> None:
    for index in range(10):
        client.cookies.clear()
        response = client.post(
            "/api/auth/register",
            json=register_payload(email=f"u{index}@example.com", username=f"user_{index}"),
        )
        assert response.status_code == 201

    blocked = client.post(
        "/api/auth/register", json=register_payload(email="x@example.com", username="user_x")
    )

    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "REGISTER_RATE_LIMITED"
