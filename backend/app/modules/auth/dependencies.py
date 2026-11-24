"""Dependency lấy người dùng hiện tại từ JWT access token."""

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.common.exceptions import UnauthorizedException
from app.core.database import get_db
from app.core.security import TOKEN_TYPE, decode_access_token
from app.modules.users.models import User
from app.modules.users.repository import get_user_by_id

# auto_error=False để tự trả về lỗi theo format chuẩn của dự án.
bearer_scheme = HTTPBearer(
    auto_error=False,
    description=(
        "JWT access token. Nhấn **Authorize** trên Swagger UI và dán token "
        "(lấy từ `POST /auth/login`) để gọi các API cần đăng nhập."
    ),
)

UNAUTHORIZED_MESSAGE = "Không có quyền truy cập. Vui lòng đăng nhập."
INVALID_TOKEN_MESSAGE = "Access token không hợp lệ hoặc đã hết hạn."


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Xác thực Bearer token và trả về user tương ứng.

    Raises:
        UnauthorizedException: 401 nếu thiếu token, token không hợp lệ/hết hạn
            hoặc user trong token không còn tồn tại.
    """
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedException(UNAUTHORIZED_MESSAGE)

    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.PyJWTError:
        raise UnauthorizedException(INVALID_TOKEN_MESSAGE) from None

    if payload.get("type") != TOKEN_TYPE or not payload.get("sub"):
        raise UnauthorizedException(INVALID_TOKEN_MESSAGE)

    try:
        user_id = int(payload["sub"])
    except (TypeError, ValueError):
        raise UnauthorizedException(INVALID_TOKEN_MESSAGE) from None

    user = get_user_by_id(db, user_id)
    if user is None:
        raise UnauthorizedException(INVALID_TOKEN_MESSAGE)

    return user
