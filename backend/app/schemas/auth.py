import re
from typing import Annotated
from uuid import UUID

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
    field_validator,
)

Username = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        to_lower=True,
        min_length=3,
        max_length=30,
        pattern=r"^[a-z0-9_]+$",
    ),
]
Password = Annotated[str, StringConstraints(min_length=8, max_length=128)]
PHONE_PATTERN = re.compile(r"^(?:0|\+84)\d{8,10}$")


class RegisterRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    email: EmailStr
    username: Username
    full_name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=2, max_length=120)
    ] = Field(
        validation_alias=AliasChoices("fullName", "full_name"), serialization_alias="fullName"
    )
    phone: Annotated[str | None, StringConstraints(strip_whitespace=True, max_length=20)] = None
    password: Password
    accept_terms: bool = Field(
        validation_alias=AliasChoices("acceptTerms", "accept_terms"),
        serialization_alias="acceptTerms",
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return value.lower()

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value: object) -> object:
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str | None) -> str | None:
        if not value:
            return None
        normalized = re.sub(r"[.\s-]", "", value)
        if not PHONE_PATTERN.fullmatch(normalized):
            raise ValueError("Số điện thoại chưa đúng định dạng.")
        return normalized

    @field_validator("accept_terms")
    @classmethod
    def require_terms_acceptance(cls, value: bool) -> bool:
        if not value:
            raise ValueError("Bạn cần đồng ý với Điều khoản sử dụng.")
        return value


class LoginRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    identifier: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=3, max_length=255)
    ]
    password: Password
    remember_me: bool = Field(
        default=False,
        validation_alias=AliasChoices("rememberMe", "remember_me"),
        serialization_alias="rememberMe",
    )

    @field_validator("identifier")
    @classmethod
    def normalize_identifier(cls, value: str) -> str:
        return value.lower()


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    email: EmailStr
    username: str
    full_name: str = Field(serialization_alias="fullName")
    phone: str | None


class HealthResponse(BaseModel):
    status: str
    database: str
