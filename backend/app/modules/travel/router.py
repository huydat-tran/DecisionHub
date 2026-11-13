"""Router cho module Travel.

Cung cấp các API theo chuẩn thiết kế:
  - GET  /api/v1/travel/quick-search
  - GET  /api/v1/travel/{place_id}
  - POST /api/v1/travel/recommend
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.responses import success_response
from app.core.database import get_db
from app.modules.travel.schemas import (
    TravelDecisionResponse,
    TravelPlaceDetail,
    TravelQuickSearchItem,
    TravelRecommendRequest,
)
from app.modules.travel.service import (
    get_travel_place_detail,
    get_travel_recommendations,
    quick_search_travel,
)

router = APIRouter(prefix="/api/v1/travel", tags=["Travel"])


@router.get(
    "/quick-search",
    summary="Tìm kiếm nhanh địa điểm du lịch",
    response_model=dict,
)
def quick_search(
    keyword: str | None = Query(None, description="Từ khóa tìm kiếm theo tên, tỉnh/thành, mô tả"),
    region: str | None = Query(None, description="Khu vực (Bắc, Trung, Nam, Tây Nguyên, Tây Nam Bộ)"),
    budget_max: int | None = Query(None, gt=0, description="Ngân sách tối đa tham khảo (VND)"),
    max_duration: float | None = Query(None, gt=0, description="Thời lượng tối đa (giờ)"),
    activity_type: str | None = Query(None, description="Loại hình trải nghiệm"),
    limit: int = Query(20, ge=1, le=50, description="Số lượng kết quả tối đa"),
    db: Session = Depends(get_db),
):
    """Tìm kiếm nhanh địa điểm du lịch kết hợp các chip lọc."""
    items: list[TravelQuickSearchItem] = quick_search_travel(
        db=db,
        keyword=keyword,
        region=region,
        budget_max=budget_max,
        max_duration=max_duration,
        activity_type=activity_type,
        limit=limit,
    )
    return success_response(
        data={
            "items": [item.model_dump() for item in items],
            "total": len(items),
            "limit": limit,
        },
        message="Lấy danh sách địa điểm du lịch thành công",
    )


@router.get(
    "/{place_id}",
    summary="Xem thông tin chi tiết địa điểm du lịch",
    response_model=dict,
)
def get_detail(
    place_id: int,
    db: Session = Depends(get_db),
):
    """Lấy chi tiết địa điểm du lịch bao gồm mô tả, điểm nổi bật và đánh giá."""
    detail: TravelPlaceDetail = get_travel_place_detail(db=db, place_id=place_id)
    return success_response(
        data=detail.model_dump(),
        message="Lấy chi tiết địa điểm du lịch thành công",
    )


@router.post(
    "/recommend",
    summary="Gợi ý địa điểm du lịch bằng Decision Engine (WSM)",
    response_model=TravelDecisionResponse,
)
def recommend_travel(
    request: TravelRecommendRequest,
    db: Session = Depends(get_db),
) -> TravelDecisionResponse:
    """Gợi ý địa điểm du lịch theo quy trình Decision Engine:

    1. Lọc điều kiện bắt buộc (ngân sách, thời lượng, khu vực).
    2. Chấm điểm 3 tiêu chí: Chi phí (40%), Sở thích (35%), Thời lượng (25%).
    3. Tính điểm WSM và xếp hạng.
    4. Trả về kết quả kèm lý do giải thích dựa trên dữ liệu thực tế.
    """
    return get_travel_recommendations(db=db, request=request)
