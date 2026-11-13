"""Router API cho module Food."""

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.food.schemas_food import (
    FoodDetailResponse,
    FoodQuickSearchFilters,
    FoodQuickSearchResponse,
    FoodRecommendRequest,
    FoodRecommendResponse,
    FoodSortBy,
    MealType,
)
from app.modules.food.services import (
    get_food_detail,
    quick_search_foods,
    recommend_foods,
)

router = APIRouter(prefix="/api/v1/food", tags=["Food"])


@router.get(
    "/quick-search",
    response_model=FoodQuickSearchResponse,
    summary="Tìm kiếm nhanh và lọc món ăn",
)
def quick_search(
    q: str | None = Query(
        default=None,
        max_length=100,
        description="Từ khóa tìm theo tên món, mô tả, nhãn hoặc nguyên liệu",
    ),
    meal_type: MealType | None = Query(
        default=None,
        description="Loại bữa ăn (breakfast, lunch, dinner, snack)",
    ),
    max_price: int | None = Query(
        default=None,
        ge=0,
        description="Giá tối đa (VND)",
    ),
    max_prep_time: int | None = Query(
        default=None,
        ge=0,
        description="Thời gian chuẩn bị tối đa (phút)",
    ),
    excluded_ingredients: list[str] | None = Query(
        default=None,
        description="Nguyên liệu cần tránh (truyền lặp tham số hoặc phân tách bằng dấu phẩy)",
    ),
    tags: list[str] | None = Query(
        default=None,
        description="Nhãn món ăn cần lọc (VD: chay, cay)",
    ),
    sort_by: FoodSortBy = Query(
        default=FoodSortBy.RELEVANCE,
        description="Sắp xếp theo relevance, price_asc hoặc prep_time_asc",
    ),
    limit: int = Query(default=20, ge=1, le=100, description="Số kết quả tối đa (1-100)"),
    offset: int = Query(default=0, ge=0, description="Vị trí bắt đầu phân trang"),
    db: Session = Depends(get_db),
) -> FoodQuickSearchResponse:
    """Nhận bộ lọc tìm kiếm nhanh từ client và trả về danh sách món ăn phù hợp."""
    filters = FoodQuickSearchFilters(
        q=q,
        meal_type=meal_type,
        max_price=max_price,
        max_prep_time=max_prep_time,
        excluded_ingredients=excluded_ingredients or [],
        tags=tags or [],
        sort_by=sort_by,
    )
    data, message = quick_search_foods(db=db, filters=filters, limit=limit, offset=offset)
    return FoodQuickSearchResponse(message=message, data=data)


@router.post(
    "/recommend",
    response_model=FoodRecommendResponse,
    summary="Gợi ý món ăn theo tiêu chí (WSM)",
)
def recommend(
    payload: FoodRecommendRequest,
    db: Session = Depends(get_db),
) -> FoodRecommendResponse:
    """Nhận tiêu chí từ client, lọc điều kiện bắt buộc, chấm điểm WSM và xếp hạng Top N."""
    data, message = recommend_foods(db=db, payload=payload)
    return FoodRecommendResponse(message=message, data=data)


@router.get(
    "/{food_id}",
    response_model=FoodDetailResponse,
    summary="Xem chi tiết món ăn",
)
def get_food(
    food_id: int = Path(..., gt=0, description="ID món ăn"),
    db: Session = Depends(get_db),
) -> FoodDetailResponse:
    """Trả về thông tin chi tiết của một món ăn theo ID."""
    food = get_food_detail(db=db, food_id=food_id)
    return FoodDetailResponse(message="Lấy thông tin món ăn thành công.", data=food)
