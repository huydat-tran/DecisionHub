"""Nghiệp vụ hồ sơ cá nhân (module Users)."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.common.exceptions import DecisionHubException
from app.modules.users.models import User
from app.modules.users.repository import get_user_by_username
from app.modules.users.schemas import UpdateProfileRequest, UserProfile


def to_user_profile(user: User) -> UserProfile:
    """Chuyển model User sang schema trả về (không lộ password_hash)."""
    return UserProfile(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role.name,
        created_at=user.created_at,
    )


def get_profile(user: User) -> UserProfile:
    """Trả về hồ sơ của người dùng hiện tại."""
    return to_user_profile(user)


def update_profile(db: Session, user: User, data: UpdateProfileRequest) -> UserProfile:
    """Cập nhật hồ sơ của người dùng hiện tại (trước mắt chỉ đổi username).

    Raises:
        DecisionHubException: 409 nếu username đã thuộc tài khoản khác,
            400 nếu request không có trường nào cần cập nhật.
    """
    if data.username is None:
        raise DecisionHubException(
            message="Không có trường nào được cập nhật.",
            status_code=400,
        )

    if data.username != user.username:
        existing = get_user_by_username(db, data.username)
        if existing is not None and existing.id != user.id:
            raise DecisionHubException(
                message="Username đã được sử dụng.",
                status_code=409,
            )

        user.username = data.username

    try:
        db.commit()
    except IntegrityError:
        # Request cập nhật chạy song song: unique constraint chặn trường hợp trùng.
        db.rollback()
        raise DecisionHubException(
            message="Username đã được sử dụng.",
            status_code=409,
        ) from None
    except Exception:
        db.rollback()
        raise

    db.refresh(user)
    return to_user_profile(user)
