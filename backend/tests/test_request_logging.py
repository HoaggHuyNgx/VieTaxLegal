import json
import logging

from fastapi.testclient import TestClient

from app.core.logging import JsonFormatter
from app.main import app


def test_response_carries_generated_request_id() -> None:
    response = TestClient(app).get("/api/health")

    assert len(response.headers["X-Request-ID"]) == 32


def test_valid_incoming_request_id_is_echoed() -> None:
    response = TestClient(app).get("/api/health", headers={"X-Request-ID": "abc-123"})

    assert response.headers["X-Request-ID"] == "abc-123"


def test_unsafe_incoming_request_id_is_replaced() -> None:
    response = TestClient(app).get("/api/health", headers={"X-Request-ID": "bad id\twith space"})

    assert response.headers["X-Request-ID"] != "bad id\twith space"
    assert len(response.headers["X-Request-ID"]) == 32


def test_access_log_has_path_status_and_no_query(caplog) -> None:
    with caplog.at_level(logging.INFO, logger="app.access"):
        TestClient(app).get("/api/health?token=secret")

    messages = [r.getMessage() for r in caplog.records if r.name == "app.access"]
    assert any("GET /api/health ->" in m for m in messages)
    assert not any("secret" in m for m in messages)


def test_json_formatter_emits_parseable_line() -> None:
    record = logging.LogRecord("x", logging.WARNING, __file__, 1, "tiếng Việt %s", ("ok",), None)
    record.request_id = "rid"

    payload = json.loads(JsonFormatter().format(record))

    assert payload["message"] == "tiếng Việt ok"
    assert payload["request_id"] == "rid"
    assert payload["level"] == "WARNING"


def test_cors_preflight_allows_patch_for_admin_routes() -> None:
    response = TestClient(app).options(
        "/api/admin/users/x",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "PATCH"},
    )

    assert response.status_code == 200
    assert "PATCH" in response.headers["access-control-allow-methods"]
