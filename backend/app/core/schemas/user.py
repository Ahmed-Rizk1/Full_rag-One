import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None
    role: str = "user"
    is_verified: bool = False


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UpdateSettingsRequest(BaseModel):
    openai_api_key: str | None = None
    groq_api_key: str | None = None
    preferred_provider: str | None = None


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str | None
    role: str
    is_verified: bool
    preferred_provider: str | None
    has_openai_key: bool = False
    has_groq_key: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def compute_key_flags(cls, data: Any) -> Any:
        # Convert ORM object or dict to allow setting has_openai_key and has_groq_key
        if isinstance(data, dict):
            data["has_openai_key"] = bool(data.get("openai_api_key"))
            data["has_groq_key"] = bool(data.get("groq_api_key"))
        else:
            # For ORM object, we can set properties on a dict/copy or dynamic attrs
            # Pydantic mode="before" validator expects either the raw object or a dict.
            # Returning an object with dynamically set properties works too,
            # but it is safer to construct/return a dict or set the attrs.
            setattr(data, "has_openai_key", bool(getattr(data, "openai_api_key", None)))
            setattr(data, "has_groq_key", bool(getattr(data, "groq_api_key", None)))
        return data

