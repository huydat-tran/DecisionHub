"""Router API cho module Food."""

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.food.schemas_food import FoodDetailResponse, FoodListResponse
from app.modules.food.services import get_all_foods, get_food_detail

router = APIRouter(prefix="/api/v1/food", tags=["Food"])


@router.get(
    "",
    response_model=FoodListResponse,
    summary="Lấy danh sách tất cả món ăn",
)
def list_foods(
    db: Session = Depends(get_db),
) -> FoodListResponse:
    """Trả về danh sách toàn bộ món ăn đang hoạt động."""
    foods = get_all_foods(db=db)
    return FoodListResponse(message="Lấy danh sách món ăn thành công.", data=foods)


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
