"""Nghiệp vụ đăng ký / đăng nhập (module Auth)."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.common.exceptions import DecisionHubException
from app.core.security import create_access_token, hash_password, verify_password
from app.modules.auth.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenData,
    UserData,
)
from app.modules.users.repository import (
    create_user,
    get_role_by_name,
    get_user_by_email,
    get_user_by_username,
)

# Role được cấp mặc định khi đăng ký. Client không được tự chọn role.
DEFAULT_ROLE_NAME = "USER"

# Thông báo chung cho mọi lỗi đăng nhập để không tiết lộ email có tồn tại hay không.
INVALID_CREDENTIALS_MESSAGE = "Email hoặc mật khẩu không đúng."


def _to_user_data(user) -> UserData:
    """Chuyển model User sang schema trả về (không lộ password_hash)."""
    return UserData(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role.name,
        created_at=user.created_at,
    )


def register_user(db: Session, data: RegisterRequest) -> UserData:
    """Đăng ký tài khoản mới với role USER.

    Raises:
        DecisionHubException: 409 nếu email đã tồn tại, 500 nếu thiếu role USER.
    """
    if get_user_by_email(db, data.email) is not None:
        raise DecisionHubException(
            message="Email đã được đăng ký.",
            status_code=409,
        )

    if get_user_by_username(db, data.username) is not None:
        raise DecisionHubException(
            message="Username đã được sử dụng.",
            status_code=409,
        )

    role = get_role_by_name(db, DEFAULT_ROLE_NAME)
    if role is None:
        raise DecisionHubException(
            message=f"Không tìm thấy vai trò '{DEFAULT_ROLE_NAME}'. Vui lòng kiểm tra dữ liệu seed.",
            status_code=500,
        )

    password_hash = hash_password(data.password)
    try:
        user = create_user(
            db,
            username=data.username,
            email=data.email,
            password_hash=password_hash,
            role_id=role.id,
        )
        db.commit()
    except IntegrityError:
        # Hai request đăng ký cùng email/username gần như đồng thời: unique constraint
        # chặn request thứ hai dù đã kiểm tra tồn tại ở trên.
        db.rollback()
        raise DecisionHubException(
            message="Email hoặc username đã được đăng ký.",
            status_code=409,
        ) from None
    except Exception:
        db.rollback()
        raise

    return _to_user_data(user)


def login_user(db: Session, data: LoginRequest) -> TokenData:
    """Xác thực thông tin đăng nhập và tạo access token.

    Raises:
        DecisionHubException: 401 khi email không tồn tại hoặc mật khẩu sai.
    """
    user = get_user_by_email(db, data.email)
    if user is None or not verify_password(data.password, user.password_hash):
        raise DecisionHubException(
            message=INVALID_CREDENTIALS_MESSAGE,
            status_code=401,
        )

    access_token = create_access_token(user_id=user.id)
    return TokenData(
        access_token=access_token,
        token_type="bearer",
        user=_to_user_data(user),
    )
