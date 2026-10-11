import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_reject_insecure_jwt_secret() -> None:
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings(database_url="sqlite+pysqlite://", jwt_secret="too-short")


def test_settings_reject_wildcard_cors_with_cookie_auth() -> None:
    with pytest.raises(ValidationError, match="CORS_ORIGINS"):
        Settings(
            database_url="sqlite+pysqlite://",
            jwt_secret="a-secure-test-secret-with-at-least-32-characters",
            cors_origins="*",
        )


def test_settings_reject_non_positive_login_throttle_limits() -> None:
    with pytest.raises(ValidationError, match="Login throttle"):
        Settings(
            database_url="sqlite+pysqlite://",
            jwt_secret="a-secure-test-secret-with-at-least-32-characters",
            login_max_failed_attempts=0,
        )


def test_settings_normalizes_supabase_connection_string() -> None:
    settings = Settings(
        database_url=(
            "postgresql://postgres.project:password@aws-0-region.pooler.supabase.com:5432/postgres"
        ),
        jwt_secret="a-secure-test-secret-with-at-least-32-characters",
    )

    assert settings.database_url.startswith("postgresql+psycopg://")
    assert settings.database_url.endswith("?sslmode=require")
