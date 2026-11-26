"""Nghiệp vụ lấy danh sách và xem chi tiết món ăn (module Food)."""

from sqlalchemy.orm import Session

from app.common.exceptions import ResourceNotFoundException
from app.modules.food.repository_food import get_active_food_by_id, get_active_foods
from app.modules.food.schemas_food import FoodOut


def get_all_foods(db: Session) -> list[FoodOut]:
    """Lấy danh sách tất cả món ăn đang hoạt động."""
    foods = get_active_foods(db)
    return [FoodOut.model_validate(food) for food in foods]


def get_food_detail(db: Session, food_id: int) -> FoodOut:
    """Lấy thông tin chi tiết của một món ăn đang hoạt động theo ID."""
    food = get_active_food_by_id(db, food_id)
    if food is None:
        raise ResourceNotFoundException("Món ăn", food_id)
    return FoodOut.model_validate(food)
