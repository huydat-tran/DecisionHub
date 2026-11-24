"""Router API cho module Users."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.openapi import ResponsesDict, error_example, error_response
from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.users.models import User
from app.modules.users.schemas import ProfileResponse, UpdateProfileRequest
from app.modules.users.service import get_profile, update_profile

router = APIRouter(prefix="/users", tags=["Users"])

MY_PROFILE_DESCRIPTION = """
Lấy thông tin tài khoản của người dùng đang đăng nhập.

**Yêu cầu xác thực**

Endpoint này yêu cầu Bearer token. Gửi header
`Authorization: Bearer <access_token>` (token lấy từ `POST /auth/login`).
Trên Swagger UI: bấm nút **Authorize** ở góc trên bên phải, dán access token
vào ô `value` của scheme `HTTPBearer` rồi bấm **Authorize** và **Close**.

Response không bao gồm `password` hay `password_hash`.
"""

MY_PROFILE_RESPONSES: ResponsesDict = {
    401: error_response(
        "Thiếu access token, token không hợp lệ/hết hạn, hoặc tài khoản "
        "trong token không còn tồn tại.",
        error_example(
            message="Không có quyền truy cập. Vui lòng đăng nhập.",
            error_code="UNAUTHORIZED",
            path="/users/me",
        ),
    ),
}


@router.get(
    "/me",
    response_model=ProfileResponse,
    summary="Lấy thông tin tài khoản hiện tại",
    description=MY_PROFILE_DESCRIPTION,
    responses=MY_PROFILE_RESPONSES,
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
