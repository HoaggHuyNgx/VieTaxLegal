import re
from functools import lru_cache
from typing import Self

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "VieTaxLegal API"
    app_env: str = "development"
    api_prefix: str = "/api"
    database_url: str
    jwt_secret: SecretStr
    jwt_algorithm: str = "HS256"
    session_cookie_name: str = "vietaxlegal_session"  # short-lived access JWT
    refresh_cookie_name: str = "vietaxlegal_refresh"  # opaque, rotating, stored hashed
    access_token_minutes: int = 15
    remember_me_days: int = 30  # refresh-token lifetime with "remember me"
    session_token_hours: int = 24  # refresh-token lifetime without it
    register_max_per_hour: int = 10  # per client address
    cors_origins: str = "http://localhost:3000"
    log_level: str = "INFO"
    log_json: bool = False
    chat_provider: str = "anthropic"
    chat_model: str = "claude-sonnet-5"
    anthropic_api_key: SecretStr | None = None
    openai_api_key: SecretStr | None = None
    chat_max_output_tokens: int = 1500
    chat_history_messages: int = 20
    chat_rate_limit_per_minute: int = 10
    chat_daily_message_limit: int = 100
    rag_enabled: bool = False
    rag_chunk_set: str = "article"
    rag_top_k: int = 5
    rag_retrieval_mode: str = "hybrid"  # dense | sparse | hybrid (dense + sparse fused with RRF)
    rag_min_similarity: float = 0.0
    # Only return documents a person marked in_force in the manifest. Turn off for dev only.
    rag_require_in_force: bool = True
    # Model that writes eval questions. Blank = CHAT_MODEL (set a different one to limit bias).
    eval_generator_model: str = ""
    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int | None = None
    embedding_batch_size: int = 64
    qdrant_url: str = "http://127.0.0.1:6333"
    qdrant_api_key: SecretStr | None = None
    login_max_failed_attempts: int = 5
    login_attempt_window_minutes: int = 15

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: object) -> object:
        if not isinstance(value, str):
            return value

        normalized = value.strip()
        if normalized.startswith("postgres://"):
            normalized = normalized.replace("postgres://", "postgresql+psycopg://", 1)
        elif normalized.startswith("postgresql://"):
            normalized = normalized.replace("postgresql://", "postgresql+psycopg://", 1)

        if "supabase.com" in normalized and "sslmode=" not in normalized:
            separator = "&" if "?" in normalized else "?"
            normalized = f"{normalized}{separator}sslmode=require"

        return normalized

    @field_validator("chat_provider", "chat_model", mode="before")
    @classmethod
    def strip_chat_identifiers(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("rag_chunk_set", mode="before")
    @classmethod
    def normalize_chunk_set(cls, value: object) -> object:
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("embedding_dimensions", mode="before")
    @classmethod
    def blank_embedding_dimensions_is_none(cls, value: object) -> object:
        return None if isinstance(value, str) and not value.strip() else value

    @field_validator("qdrant_api_key", mode="before")
    @classmethod
    def blank_qdrant_api_key_is_none(cls, value: object) -> object:
        # `.env.example` ships `QDRANT_API_KEY=` for the local, unauthenticated server.
        return None if isinstance(value, str) and not value.strip() else value

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @model_validator(mode="after")
    def validate_security_settings(self) -> Self:
        secret = self.jwt_secret.get_secret_value()
        if len(secret) < 32 or secret.startswith("replace-with-"):
            raise ValueError("JWT_SECRET phải là một chuỗi ngẫu nhiên có ít nhất 32 ký tự.")
        if "*" in self.cors_origin_list:
            raise ValueError("CORS_ORIGINS không được dùng '*' khi xác thực bằng cookie.")
        if self.jwt_algorithm not in ("HS256", "HS384", "HS512"):
            raise ValueError("JWT_ALGORITHM must be HS256, HS384 or HS512.")
        if self.log_level.upper() not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            raise ValueError("LOG_LEVEL must be DEBUG, INFO, WARNING, ERROR or CRITICAL.")
        if self.chat_max_output_tokens < 1 or self.chat_max_output_tokens > 8192:
            raise ValueError("CHAT_MAX_OUTPUT_TOKENS must be between 1 and 8192.")
        if self.chat_history_messages < 1 or self.chat_history_messages > 100:
            raise ValueError("CHAT_HISTORY_MESSAGES must be between 1 and 100.")
        if self.chat_rate_limit_per_minute < 1 or self.chat_daily_message_limit < 1:
            raise ValueError("Chat limits must be greater than zero.")
        if min(self.access_token_minutes, self.register_max_per_hour) < 1:
            raise ValueError("ACCESS_TOKEN_MINUTES and REGISTER_MAX_PER_HOUR must be positive.")
        if self.login_max_failed_attempts < 1 or self.login_attempt_window_minutes < 1:
            raise ValueError("Login throttle limits must be greater than zero.")
        if not self.chat_provider.strip() or not self.chat_model.strip():
            raise ValueError("CHAT_PROVIDER and CHAT_MODEL must not be blank.")
        if not re.fullmatch(r"[a-z0-9_]{1,32}", self.rag_chunk_set):
            raise ValueError("RAG_CHUNK_SET must be 1-32 chars of a-z, 0-9 or underscore.")
        if self.rag_top_k < 1 or self.rag_top_k > 50:
            raise ValueError("RAG_TOP_K must be between 1 and 50.")
        if self.rag_retrieval_mode not in ("dense", "sparse", "hybrid"):
            raise ValueError("RAG_RETRIEVAL_MODE must be dense, sparse or hybrid.")
        if not 0.0 <= self.rag_min_similarity <= 1.0:
            raise ValueError("RAG_MIN_SIMILARITY must be between 0 and 1.")
        if self.embedding_provider not in ("openai", "bkai", "fake"):
            raise ValueError("EMBEDDING_PROVIDER must be openai, bkai or fake.")
        if not 1 <= self.embedding_batch_size <= 512:
            raise ValueError("EMBEDDING_BATCH_SIZE must be between 1 and 512.")
        if self.embedding_dimensions is not None and self.embedding_dimensions < 1:
            raise ValueError("EMBEDDING_DIMENSIONS must be positive.")
        if not self.qdrant_url.startswith(("http://", "https://")):
            raise ValueError("QDRANT_URL must start with http:// or https://.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
