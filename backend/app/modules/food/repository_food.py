"""Truy vấn dữ liệu món ăn (module Food)."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.food.models_food import Food


def get_active_foods(db: Session) -> list[Food]:
    """Lấy danh sách tất cả món ăn đang hoạt động kèm nguyên liệu."""
    stmt = (
        select(Food)
        .options(selectinload(Food.ingredients))
        .where(Food.is_active.is_(True))
        .order_by(Food.id.asc())
    )
    return list(db.scalars(stmt).all())


def get_active_food_by_id(db: Session, food_id: int) -> Food | None:
    """Lấy một món ăn đang hoạt động theo id (kèm nguyên liệu), trả về None nếu không tồn tại."""
    stmt = (
        select(Food)
        .options(selectinload(Food.ingredients))
        .where(Food.id == food_id, Food.is_active.is_(True))
    )
    return db.scalar(stmt)
