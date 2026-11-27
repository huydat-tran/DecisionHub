"""Truy vấn dữ liệu món ăn và nguyên liệu (module Food)."""

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.modules.food.models_food import Food, Ingredient


def get_foods(db: Session, *, include_inactive: bool = False) -> list[Food]:
    """Lấy danh sách món ăn kèm nguyên liệu (mặc định chỉ lấy món đang hoạt động)."""
    stmt = select(Food).options(selectinload(Food.ingredients)).order_by(Food.id.asc())
    if not include_inactive:
        stmt = stmt.where(Food.is_active.is_(True))
    return list(db.scalars(stmt).all())


def get_food_by_id(
    db: Session,
    food_id: int,
    *,
    include_inactive: bool = False,
) -> Food | None:
    """Lấy một món ăn theo id kèm nguyên liệu, trả về None nếu không tồn tại."""
    stmt = (
        select(Food)
        .options(selectinload(Food.ingredients))
        .where(Food.id == food_id)
    )
    if not include_inactive:
        stmt = stmt.where(Food.is_active.is_(True))
    return db.scalar(stmt)


def get_or_create_ingredients(db: Session, names: list[str]) -> list[Ingredient]:
    """Tra cứu nguyên liệu theo tên (không phân biệt hoa thường) và tạo mới nếu chưa có."""
    if not names:
        return []

    lower_names = [name.lower() for name in names]
    stmt = select(Ingredient).where(func.lower(Ingredient.name).in_(lower_names))
    existing = {ing.name.lower(): ing for ing in db.scalars(stmt).all()}

    resolved: list[Ingredient] = []
    for name in names:
        key = name.lower()
        ingredient = existing.get(key)
        if ingredient is None:
            ingredient = Ingredient(name=name)
            db.add(ingredient)
            existing[key] = ingredient
        resolved.append(ingredient)

    db.flush()
    return resolved


def create_food_record(
    db: Session,
    *,
    name: str,
    price: int,
    meal_type: str,
    prep_time: int | None,
    description: str | None,
    image_url: str | None,
    tags: list[str],
    ingredient_names: list[str],
    is_active: bool,
) -> Food:
    """Tạo mới bản ghi món ăn và liên kết nguyên liệu."""
    ingredients = get_or_create_ingredients(db, ingredient_names)
    food = Food(
        name=name,
        price=Decimal(price),
        meal_type=meal_type,
        prep_time=prep_time,
        description=description,
        image_url=image_url,
        tags=tags,
        is_active=is_active,
        ingredients=ingredients,
    )
    db.add(food)
    db.flush()
    db.refresh(food)
    return food


def update_food_record(
    db: Session,
    food: Food,
    *,
    updates: dict[str, object],
    ingredient_names: list[str] | None = None,
) -> Food:
    """Cập nhật các trường của món ăn và danh sách nguyên liệu (nếu truyền vào)."""
    for field, value in updates.items():
        if field == "price" and isinstance(value, (int, Decimal)) and not isinstance(value, bool):
            food.price = Decimal(value)
        else:
            setattr(food, field, value)

    if ingredient_names is not None:
        food.ingredients = get_or_create_ingredients(db, ingredient_names)

    db.flush()
    db.refresh(food)
    return food


def delete_food_record(db: Session, food: Food) -> None:
    """Xoá bản ghi món ăn khỏi cơ sở dữ liệu."""
    db.delete(food)
    db.flush()
