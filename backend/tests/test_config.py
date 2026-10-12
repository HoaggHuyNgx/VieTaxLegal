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


def _rag_settings(**overrides) -> Settings:
    return Settings(
        database_url="sqlite+pysqlite://",
        jwt_secret="a-secure-test-secret-with-at-least-32-characters",
        **overrides,
    )


def test_rag_settings_defaults_are_safe_and_local() -> None:
    settings = _rag_settings()

    assert settings.rag_enabled is False
    assert settings.qdrant_url == "http://127.0.0.1:6333"
    assert settings.qdrant_api_key is None
    assert settings.rag_chunk_set == "article"


def test_rag_settings_blank_qdrant_api_key_means_none() -> None:
    assert _rag_settings(qdrant_api_key="  ").qdrant_api_key is None


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"rag_chunk_set": "Bad Name!"}, "RAG_CHUNK_SET"),
        ({"rag_top_k": 0}, "RAG_TOP_K"),
        ({"rag_min_similarity": 1.5}, "RAG_MIN_SIMILARITY"),
        ({"qdrant_url": "127.0.0.1:6333"}, "QDRANT_URL"),
    ],
)
def test_rag_settings_reject_invalid_values(overrides: dict, message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        _rag_settings(**overrides)


def test_rag_retrieval_mode_defaults_to_hybrid_and_rejects_unknown_values() -> None:
    assert _rag_settings().rag_retrieval_mode == "hybrid"
    assert _rag_settings(rag_retrieval_mode="sparse").rag_retrieval_mode == "sparse"
    with pytest.raises(ValidationError, match="RAG_RETRIEVAL_MODE"):
        _rag_settings(rag_retrieval_mode="graph")


def test_settings_reject_unsupported_jwt_algorithm() -> None:
    with pytest.raises(ValidationError, match="JWT_ALGORITHM"):
        Settings(
            database_url="sqlite+pysqlite://",
            jwt_secret="a-secure-test-secret-with-at-least-32-characters",
            jwt_algorithm="none",
        )
