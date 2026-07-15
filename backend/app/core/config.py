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
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
