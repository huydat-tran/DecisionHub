"""Nghiệp vụ CRUD danh sách và chi tiết món ăn (module Food)."""

from sqlalchemy.orm import Session

from app.common.exceptions import BadRequestException, ResourceNotFoundException
from app.modules.food.repository_food import (
    create_food_record,
    delete_food_record,
    get_food_by_id,
    get_foods,
    update_food_record,
)
from app.modules.food.schemas_food import FoodCreate, FoodOut, FoodUpdate


def get_all_foods(db: Session, *, include_inactive: bool = False) -> list[FoodOut]:
    """Lấy danh sách món ăn (mặc định chỉ món đang hoạt động; Admin có thể lấy tất cả)."""
    foods = get_foods(db, include_inactive=include_inactive)
    return [FoodOut.model_validate(food) for food in foods]


def get_food_detail(
    db: Session,
    food_id: int,
    *,
    include_inactive: bool = False,
) -> FoodOut:
    """Lấy thông tin chi tiết của một món ăn theo ID."""
    food = get_food_by_id(db, food_id, include_inactive=include_inactive)
    if food is None:
        raise ResourceNotFoundException("Món ăn", food_id)
    return FoodOut.model_validate(food)


def create_food(db: Session, payload: FoodCreate) -> FoodOut:
    """Tạo mới một món ăn trong danh mục."""
    try:
        food = create_food_record(
            db,
            name=payload.name,
            price=payload.price,
            meal_type=payload.meal_type,
            prep_time=payload.prep_time,
            description=payload.description,
            image_url=payload.image_url,
            tags=payload.tags,
            ingredient_names=payload.ingredients,
            is_active=payload.is_active,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    created = get_food_by_id(db, food.id, include_inactive=True)
    return FoodOut.model_validate(created or food)


def update_food(db: Session, food_id: int, payload: FoodUpdate) -> FoodOut:
    """Cập nhật thông tin món ăn theo ID."""
    food = get_food_by_id(db, food_id, include_inactive=True)
    if food is None:
        raise ResourceNotFoundException("Món ăn", food_id)

    fields_set = payload.model_fields_set
    if not fields_set:
        raise BadRequestException("Không có trường dữ liệu nào cần cập nhật.")

    updates: dict[str, object] = {}
    for field in (
        "name",
        "price",
        "meal_type",
        "prep_time",
        "description",
        "image_url",
        "tags",
        "is_active",
    ):
        if field in fields_set:
            value = getattr(payload, field)
            # Không cho phép ghi đè null vào các cột NOT NULL trong database.
            if field in ("name", "price", "meal_type", "is_active") and value is None:
                raise BadRequestException(f"Trường '{field}' không được để trống.")
            updates[field] = value

    ingredient_names = payload.ingredients if "ingredients" in fields_set else None

    try:
        updated = update_food_record(
            db,
            food,
            updates=updates,
            ingredient_names=ingredient_names,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    refreshed = get_food_by_id(db, updated.id, include_inactive=True)
    return FoodOut.model_validate(refreshed or updated)


def delete_food(db: Session, food_id: int) -> int:
    """Xoá món ăn theo ID khỏi cơ sở dữ liệu."""
    food = get_food_by_id(db, food_id, include_inactive=True)
    if food is None:
        raise ResourceNotFoundException("Món ăn", food_id)

    try:
        delete_food_record(db, food)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return food_id
