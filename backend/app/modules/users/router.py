"""Router API cho module Users."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.users.models import User
from app.modules.users.schemas import ProfileResponse, UpdateProfileRequest
from app.modules.users.service import get_profile, update_profile

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=ProfileResponse,
    summary="Lấy thông tin tài khoản hiện tại",
)
def read_my_profile(
    current_user: User = Depends(get_current_user),
) -> ProfileResponse:
    """Trả về hồ sơ của người dùng đang đăng nhập (không có password_hash)."""
    return ProfileResponse(message="Lấy thông tin tài khoản thành công.", data=get_profile(current_user))


@router.patch(
    "/me",
    response_model=ProfileResponse,
    summary="Cập nhật hồ sơ tài khoản hiện tại",
)
def patch_my_profile(
    data: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProfileResponse:
    """Cập nhật hồ sơ của người dùng đang đăng nhập (hiện chỉ hỗ trợ username)."""
    profile = update_profile(db, current_user, data)
    return ProfileResponse(message="Cập nhật hồ sơ thành công.", data=profile)
