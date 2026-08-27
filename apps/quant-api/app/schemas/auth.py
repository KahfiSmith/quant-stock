from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class DeleteAccountRequest(BaseModel):
    password: str = Field(min_length=1, max_length=128)


class UpdateProfileRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    theme_preference: str | None = Field(default=None, pattern="^(light|dark|system)$")
    timezone: str | None = Field(default=None, min_length=1, max_length=64)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    name: str
    theme_preference: str
    timezone: str
    role: str
    is_email_verified: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AuthPayload(BaseModel):
    access_token: str
    expires_in: int
    user: UserResponse
