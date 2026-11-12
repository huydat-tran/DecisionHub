"""Các thành phần bảo mật dùng chung: hash mật khẩu và tạo/kiểm tra JWT access token."""

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.core.config import settings

# Access token dùng để xác thực các API cần đăng nhập.
TOKEN_TYPE = "access"


def hash_password(password: str) -> str:
    """Hash mật khẩu bằng bcrypt (salt và cost factor do thư viện tự sinh)."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Kiểm tra mật khẩu có khớp với hash đã lưu hay không."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        # Hash lưu trong DB không phải định dạng bcrypt hợp lệ.
        return False


def create_access_token(user_id: int, expires_delta: timedelta | None = None) -> str:
    """Tạo JWT access token với subject là id người dùng."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "type": TOKEN_TYPE,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Giải mã và kiểm tra JWT access token, trả về payload."""
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
