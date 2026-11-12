"""Pydantic schemas cho module Auth (đăng ký / đăng nhập)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

# bcrypt chỉ xử lý tối đa 72 byte mật khẩu (sau khi encode UTF-8).
BCRYPT_MAX_PASSWORD_BYTES = 72
MIN_PASSWORD_LENGTH = 8


class RegisterRequest(BaseModel):
    """Dữ liệu đăng ký tài khoản mới (client không được tự chọn role)."""
    username: str = Field(
        ...,
        min_length=5,
        max_length=50,
        description="Tên người dùng"
    )
    email: EmailStr = Field(..., description="Email dùng để đăng nhập")
    password: str = Field(..., min_length=MIN_PASSWORD_LENGTH)

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

    email: EmailStr
    password: str


class UserData(BaseModel):
    """Thông tin tài khoản được trả về (không chứa password / password_hash)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    role: str
    created_at: datetime


class TokenData(BaseModel):
    """Access token và thông tin tài khoản sau khi đăng nhập."""

    access_token: str
    token_type: str = "bearer"
    user: UserData


class RegisterResponse(BaseModel):
    """Response đăng ký thành công, theo format chung của dự án."""

    success: bool = True
    message: str
    data: UserData


class LoginResponse(BaseModel):
    """Response đăng nhập thành công, theo format chung của dự án."""

    success: bool = True
    message: str
    data: TokenData
