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
    session_cookie_name: str = "vietaxlegal_session"
    remember_me_days: int = 30
    session_token_hours: int = 24
    cors_origins: str = "http://localhost:3000"
    chat_provider: str = "anthropic"
    chat_model: str = "claude-sonnet-5"
    anthropic_api_key: SecretStr | None = None
    openai_api_key: SecretStr | None = None
    chat_max_output_tokens: int = 1500
    chat_history_messages: int = 20
    chat_rate_limit_per_minute: int = 10
    chat_daily_message_limit: int = 100

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
        if self.chat_max_output_tokens < 1 or self.chat_max_output_tokens > 8192:
            raise ValueError("CHAT_MAX_OUTPUT_TOKENS must be between 1 and 8192.")
        if self.chat_history_messages < 1 or self.chat_history_messages > 100:
            raise ValueError("CHAT_HISTORY_MESSAGES must be between 1 and 100.")
        if self.chat_rate_limit_per_minute < 1 or self.chat_daily_message_limit < 1:
            raise ValueError("Chat limits must be greater than zero.")
        if not self.chat_provider.strip() or not self.chat_model.strip():
            raise ValueError("CHAT_PROVIDER and CHAT_MODEL must not be blank.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
