"""Pydantic schemas cho module Auth (đăng ký / đăng nhập)."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.modules.users.schemas import UserProfile

# bcrypt chỉ xử lý tối đa 72 byte mật khẩu (sau khi encode UTF-8).
BCRYPT_MAX_PASSWORD_BYTES = 72
MIN_PASSWORD_LENGTH = 8


class RegisterRequest(BaseModel):
    """Dữ liệu đăng ký tài khoản mới (client không được tự chọn role)."""

    username: str = Field(
        ...,
        min_length=5,
        max_length=50,
        description="Tên người dùng, duy nhất trong hệ thống (tối thiểu 5, tối đa 50 ký tự)."
    )
    email: EmailStr = Field(
        ...,
        description="Email dùng để đăng nhập, duy nhất trong hệ thống."
    )
    password: str = Field(
        ...,
        min_length=MIN_PASSWORD_LENGTH,
        description=(
            f"Mật khẩu tối thiểu {MIN_PASSWORD_LENGTH} ký tự, phải có ít nhất 1 chữ cái in hoa "
            f"và 1 ký tự đặc biệt, không vượt quá {BCRYPT_MAX_PASSWORD_BYTES} byte "
            "khi mã hóa UTF-8."
        ),
    )

    @field_validator("password")
    @classmethod
    def check_password(cls, value: str) -> str:
        """Kiểm tra độ mạnh và giới hạn byte của mật khẩu."""

        if len(value.encode("utf-8")) > BCRYPT_MAX_PASSWORD_BYTES:
            raise ValueError(
                f"Mật khẩu không được vượt quá {BCRYPT_MAX_PASSWORD_BYTES} byte khi mã hóa UTF-8."
            )

        if not any(char.isupper() for char in value):
            raise ValueError("Mật khẩu phải có ít nhất 1 chữ cái in hoa.")

        if not any(not char.isalnum() for char in value):
            raise ValueError("Mật khẩu phải có ít nhất 1 ký tự đặc biệt.")

        return value


class LoginRequest(BaseModel):
    """Dữ liệu đăng nhập."""

    email: EmailStr = Field(..., description="Email đã đăng ký.")
    password: str = Field(..., description="Mật khẩu tương ứng với email.")


# Giữ tên UserData để không phá vỡ code đang dùng; nội dung giống UserProfile.
UserData = UserProfile


class TokenData(BaseModel):
    """Access token và thông tin tài khoản sau khi đăng nhập."""

    access_token: str = Field(
        ...,
        description=(
            "JWT access token, dùng gửi kèm header "
            "`Authorization: Bearer <access_token>` cho các API cần xác thực."
        ),
    )
    token_type: str = Field("bearer", description="Loại token, luôn là `bearer`.")
    user: UserData


class RegisterResponse(BaseModel):
    """Response đăng ký thành công, theo format chung của dự án."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Đăng ký thành công.",
                "data": {
                    "id": 1,
                    "username": "nguyenvanan",
                    "email": "nguyenvanan@example.com",
                    "role": "USER",
                    "created_at": "2026-11-24T10:30:00Z",
                },
            }
        }
    )

    success: bool = True
    message: str
    data: UserData


class LoginResponse(BaseModel):
    """Response đăng nhập thành công, theo format chung của dự án."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Đăng nhập thành công.",
                "data": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "user": {
                        "id": 1,
                        "username": "nguyenvanan",
                        "email": "nguyenvanan@example.com",
                        "role": "USER",
                        "created_at": "2026-11-24T10:30:00Z",
                    },
                },
            }
        }
    )

    success: bool = True
    message: str
    data: TokenData
