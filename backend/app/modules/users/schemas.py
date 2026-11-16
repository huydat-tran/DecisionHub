"""Pydantic schemas cho module Users (hồ sơ cá nhân)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserProfile(BaseModel):
    """Thông tin hồ sơ được trả về (không chứa password / password_hash)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    role: str
    created_at: datetime


class UpdateProfileRequest(BaseModel):
    """Dữ liệu cập nhật hồ sơ. Chỉ cho phép đổi username."""

    model_config = ConfigDict(extra="forbid")

    username: str | None = Field(
        None,
        min_length=5,
        max_length=50,
        description="Tên người dùng mới",
    )


class ProfileResponse(BaseModel):
    """Response hồ sơ cá nhân, theo format chung của dự án."""

    success: bool = True
    message: str
    data: UserProfile
