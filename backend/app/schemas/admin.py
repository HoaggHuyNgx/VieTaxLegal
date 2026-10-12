from datetime import datetime
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field


class AdminUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    email: EmailStr
    username: str
    full_name: str = Field(serialization_alias="fullName")
    role: str
    is_active: bool = Field(serialization_alias="isActive")
    created_at: datetime = Field(serialization_alias="createdAt")


class AdminUserUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    role: str | None = None
    is_active: bool | None = Field(
        default=None, validation_alias=AliasChoices("isActive", "is_active")
    )
