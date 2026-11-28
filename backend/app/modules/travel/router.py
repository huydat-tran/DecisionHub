"""Router API cho module Travel."""

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from app.common.exceptions import ForbiddenException
from app.common.openapi import ResponsesDict, error_example, error_response
from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.decision.service import recommend_travel
from app.modules.travel.models import TravelRegion
from app.modules.travel.schemas import (
    TravelPlaceCreateRequest,
    TravelPlaceDeleteResponse,
    TravelPlaceDetailResponse,
    TravelPlaceListResponse,
    TravelPlaceUpdateRequest,
    TravelRecommendRequest,
    TravelRecommendResponse,
)
from app.modules.travel.services import (
    create_admin_travel_place,
    delete_admin_travel_place,
    get_admin_travel_place_detail,
    list_admin_travel_places,
    replace_admin_travel_place,
    update_admin_travel_place,
)
from app.modules.users.models import User

router = APIRouter(prefix="/api/v1/travel", tags=["Travel"])

ADMIN_FORBIDDEN_MESSAGE = "Bạn không có quyền thực hiện thao tác này. Chỉ ADMIN được phép truy cập."


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Xác thực người dùng hiện tại có vai trò ADMIN hay không."""
    role_name = current_user.role.name.upper() if current_user.role else ""
    if role_name != "ADMIN":
        raise ForbiddenException(ADMIN_FORBIDDEN_MESSAGE)
    return current_user


def _admin_auth_responses(path: str) -> ResponsesDict:
    return {
        401: error_response(
            "Thiếu access token, token không hợp lệ hoặc đã hết hạn.",
            error_example(
                message="Không có quyền truy cập. Vui lòng đăng nhập.",
                error_code="UNAUTHORIZED",
                path=path,
            ),
        ),
        403: error_response(
            "Người dùng không có quyền ADMIN.",
            error_example(
                message=ADMIN_FORBIDDEN_MESSAGE,
                error_code="FORBIDDEN",
                path=path,
            ),
        ),
    }


def _not_found_response(path: str) -> dict[str, object]:
    return error_response(
        "Không tìm thấy địa điểm du lịch.",
        error_example(
            message="Địa điểm du lịch với mã 999 không tồn tại.",
            error_code="RESOURCE_NOT_FOUND",
            path=path,
        ),
    )


def _conflict_response(path: str) -> dict[str, object]:
    return error_response(
        "Tên địa điểm du lịch đã tồn tại.",
        error_example(
            message="Địa điểm 'Phố cổ Hội An' đã tồn tại.",
            error_code="CONFLICT",
            path=path,
        ),
    )


@router.post(
    "/recommend",
    response_model=TravelRecommendResponse,
    summary="Gợi ý địa điểm du lịch theo tiêu chí (WSM)",
)
def recommend(
    payload: TravelRecommendRequest,
    db: Session = Depends(get_db),  # noqa: B008
) -> TravelRecommendResponse:
    """Nhận tiêu chí từ client, lọc điều kiện ngân sách/thời lượng, chấm điểm WSM và xếp hạng Top N."""
    data, message = recommend_travel(db=db, payload=payload)
    return TravelRecommendResponse(success=True, message=message, data=data)


@router.get(
    "",
    response_model=TravelPlaceListResponse,
    summary="Lấy danh sách địa điểm du lịch (Admin)",
    responses=_admin_auth_responses("/api/v1/travel"),
)
def list_places(
    keyword: str | None = Query(default=None, description="Tìm theo tên hoặc tỉnh/thành phố"),
    region: TravelRegion | None = Query(default=None, description="Lọc theo khu vực địa lý"),
    activity_type: str | None = Query(default=None, description="Lọc theo loại hình trải nghiệm"),
    is_active: bool | None = Query(default=None, description="Lọc theo trạng thái hoạt động"),
    limit: int = Query(default=20, ge=1, le=100, description="Số bản ghi tối đa trên trang (1-100)"),
    offset: int = Query(default=0, ge=0, description="Vị trí bắt đầu phân trang (>= 0)"),
    db: Session = Depends(get_db),  # noqa: B008
    _: User = Depends(require_admin),  # noqa: B008
) -> TravelPlaceListResponse:
    """Trả về danh sách địa điểm du lịch kèm bộ lọc và phân trang (chỉ ADMIN)."""
    data = list_admin_travel_places(
        db,
        keyword=keyword,
        region=region,
        activity_type=activity_type,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )
    return TravelPlaceListResponse(
        success=True,
        message="Lấy danh sách địa điểm du lịch thành công.",
        data=data,
    )


@router.get(
    "/{place_id}",
    response_model=TravelPlaceDetailResponse,
    summary="Xem chi tiết địa điểm du lịch (Admin)",
    responses={
        **_admin_auth_responses("/api/v1/travel/1"),
        404: _not_found_response("/api/v1/travel/999"),
    },
)
def get_place(
    place_id: int = Path(..., gt=0, description="ID địa điểm du lịch"),
    db: Session = Depends(get_db),  # noqa: B008
    _: User = Depends(require_admin),  # noqa: B008
) -> TravelPlaceDetailResponse:
    """Trả về chi tiết một địa điểm du lịch theo ID (chỉ ADMIN)."""
    data = get_admin_travel_place_detail(db, place_id)
    return TravelPlaceDetailResponse(
        success=True,
        message="Lấy thông tin địa điểm du lịch thành công.",
        data=data,
    )


@router.post(
    "",
    response_model=TravelPlaceDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo mới địa điểm du lịch (Admin)",
    responses={
        **_admin_auth_responses("/api/v1/travel"),
        409: _conflict_response("/api/v1/travel"),
    },
)
def create_place(
    payload: TravelPlaceCreateRequest,
    db: Session = Depends(get_db),  # noqa: B008
    _: User = Depends(require_admin),  # noqa: B008
) -> TravelPlaceDetailResponse:
    """Thêm mới một địa điểm du lịch (chỉ ADMIN)."""
    data = create_admin_travel_place(db, payload)
    return TravelPlaceDetailResponse(
        success=True,
        message="Tạo địa điểm du lịch thành công.",
        data=data,
    )


@router.put(
    "/{place_id}",
    response_model=TravelPlaceDetailResponse,
    summary="Cập nhật toàn bộ địa điểm du lịch (Admin)",
    responses={
        **_admin_auth_responses("/api/v1/travel/1"),
        404: _not_found_response("/api/v1/travel/999"),
        409: _conflict_response("/api/v1/travel/1"),
    },
)
def replace_place(
    payload: TravelPlaceCreateRequest,
    place_id: int = Path(..., gt=0, description="ID địa điểm du lịch"),
    db: Session = Depends(get_db),  # noqa: B008
    _: User = Depends(require_admin),  # noqa: B008
) -> TravelPlaceDetailResponse:
    """Thay thế toàn bộ thông tin một địa điểm du lịch theo ID (chỉ ADMIN)."""
    data = replace_admin_travel_place(db, place_id, payload)
    return TravelPlaceDetailResponse(
        success=True,
        message="Cập nhật địa điểm du lịch thành công.",
        data=data,
    )


@router.patch(
    "/{place_id}",
    response_model=TravelPlaceDetailResponse,
    summary="Cập nhật một phần địa điểm du lịch (Admin)",
    responses={
        **_admin_auth_responses("/api/v1/travel/1"),
        400: error_response(
            "Không có trường nào được gửi để cập nhật.",
            error_example(
                message="Không có trường nào được cập nhật.",
                error_code="BAD_REQUEST",
                path="/api/v1/travel/1",
            ),
        ),
        404: _not_found_response("/api/v1/travel/999"),
        409: _conflict_response("/api/v1/travel/1"),
    },
)
def patch_place(
    payload: TravelPlaceUpdateRequest,
    place_id: int = Path(..., gt=0, description="ID địa điểm du lịch"),
    db: Session = Depends(get_db),  # noqa: B008
    _: User = Depends(require_admin),  # noqa: B008
) -> TravelPlaceDetailResponse:
    """Cập nhật một phần thông tin địa điểm du lịch theo ID (chỉ ADMIN)."""
    data = update_admin_travel_place(db, place_id, payload)
    return TravelPlaceDetailResponse(
        success=True,
        message="Cập nhật địa điểm du lịch thành công.",
        data=data,
    )


@router.delete(
    "/{place_id}",
    response_model=TravelPlaceDeleteResponse,
    summary="Xóa địa điểm du lịch (Admin)",
    responses={
        **_admin_auth_responses("/api/v1/travel/1"),
        404: _not_found_response("/api/v1/travel/999"),
        409: error_response(
            "Không thể xóa địa điểm đang được tham chiếu.",
            error_example(
                message="Không thể xóa địa điểm vì đang được dữ liệu khác tham chiếu.",
                error_code="CONFLICT",
                path="/api/v1/travel/1",
            ),
        ),
    },
)
def delete_place(
    place_id: int = Path(..., gt=0, description="ID địa điểm du lịch"),
    db: Session = Depends(get_db),  # noqa: B008
    _: User = Depends(require_admin),  # noqa: B008
) -> TravelPlaceDeleteResponse:
    """Xóa một địa điểm du lịch theo ID (chỉ ADMIN)."""
    data = delete_admin_travel_place(db, place_id)
    return TravelPlaceDeleteResponse(
        success=True,
        message="Xóa địa điểm du lịch thành công.",
        data=data,
    )
