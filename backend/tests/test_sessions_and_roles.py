from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, select, update

from app.core.errors import AppError
from app.models.refresh_token import RefreshToken
from app.models.user import ROLE_ADMIN, User
from app.schemas.admin import AdminUserUpdate
from app.services.admin import update_user
from app.services.auth.refresh_tokens import revoke_all_for_user
from tests.test_auth import create_user, register_payload

PASSWORD = "Mat-khau-an-toan-2026!"


def refresh_cookie(client: TestClient) -> str:
    return client.cookies.get("vietaxlegal_refresh")


def set_refresh_cookie(client: TestClient, token: str) -> None:
    # Drop the server-set cookie first: the jar keys cookies by domain, so a second
    # same-name cookie would sit beside it and httpx2 would keep sending the server's.
    client.cookies.delete("vietaxlegal_refresh")
    client.cookies.set("vietaxlegal_refresh", token, path="/api/auth")


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

    set_refresh_cookie(client, stolen)
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

    set_refresh_cookie(client, token)
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
    set_refresh_cookie(client, victim_refresh)
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


def test_second_tab_losing_refresh_race_keeps_the_winners_cookies(
    client: TestClient, database_session
) -> None:
    create_user(client)
    stale = refresh_cookie(client)
    assert client.post("/api/auth/refresh").status_code == 200
    winner = refresh_cookie(client)

    # Second tab still presents the token that was rotated a moment ago.
    set_refresh_cookie(client, stale)
    response = client.post("/api/auth/refresh")

    assert response.status_code == 204
    assert response.content == b""
    assert "set-cookie" not in response.headers
    live = database_session.scalars(
        select(RefreshToken).where(RefreshToken.revoked_at.is_(None))
    ).all()
    assert len(live) == 1  # family not revoked; the winner's token still works
    set_refresh_cookie(client, winner)
    assert client.post("/api/auth/refresh").status_code == 200


def test_cors_preflight_allows_patch_for_admin_routes(client: TestClient) -> None:
    response = client.options(
        "/api/admin/users/x",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "PATCH"},
    )

    assert response.status_code == 200
    assert "PATCH" in response.headers["access-control-allow-methods"]


@pytest.mark.parametrize("path", ["/api/auth/refresh", "/api/auth/logout", None])
def test_token_changes_lock_the_user_row_first(
    client: TestClient, database_session, path: str | None
) -> None:
    """Rotation and revocation must queue on one lock, or a token born during a logout survives.

    SQLite ignores FOR UPDATE, so this only checks the order the statements ask for.
    """
    create_user(client)
    user_id = UUID(client.get("/api/auth/me").json()["id"])
    steps: list[str] = []

    def record(state) -> None:
        statement = state.statement
        locked = getattr(statement, "_for_update_arg", None) is not None
        if state.is_select and locked:
            steps.append(f"lock {statement.column_descriptions[0]['entity'].__tablename__}")
        elif state.is_update:
            steps.append(f"update {statement.table.name}")

    event.listen(database_session, "do_orm_execute", record)
    if path:
        client.post(path)
    else:  # what deactivating an account does
        revoke_all_for_user(database_session, user_id)
    event.remove(database_session, "do_orm_execute", record)

    assert steps[0] == "lock users"
    assert any("refresh_tokens" in step for step in steps[1:])


def test_an_admin_demoted_meanwhile_cannot_demote_others(
    client: TestClient, database_session
) -> None:
    """Two admins demoting each other at once must not leave the system with none."""
    create_user(client, email="other@example.com", username="other_admin")
    create_user(client)
    promote(database_session, "huy_legal")
    promote(database_session, "other_admin")
    me = database_session.scalar(select(User).where(User.username == "huy_legal"))
    other = database_session.scalar(select(User).where(User.username == "other_admin"))
    database_session.execute(
        update(User)
        .where(User.id == me.id)
        .values(role="user")
        .execution_options(synchronize_session=False)
    )
    database_session.commit()

    with pytest.raises(AppError) as refused:
        update_user(database_session, me, other.id, AdminUserUpdate(role="user"))

    assert refused.value.status_code == 403
    database_session.refresh(other)
    assert other.role == ROLE_ADMIN
