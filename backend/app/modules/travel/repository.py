"""Travel data access layer.

Queries active travel places from the database (with mock fallback for recommendation),
and provides CRUD operations for travel place management.
"""

from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.modules.travel.mock_data import RAW_MOCK_TRAVEL_CANDIDATES
from app.modules.travel.models import TravelPlace, TravelRegion


def get_active_travel_places(db: Session) -> list[Any]:
    """Return active travel places from DB; fallback to mock dicts if empty."""
    try:
        stmt = (
            select(TravelPlace)
            .where(TravelPlace.is_active.is_(True), TravelPlace.estimated_cost >= 0)
            .order_by(TravelPlace.id.asc())
        )
        places = list(db.scalars(stmt).all())
        if places:
            return places
    except Exception:  # pragma: no cover
        pass
    return list(RAW_MOCK_TRAVEL_CANDIDATES)


def list_travel_places(
    db: Session,
    *,
    keyword: str | None = None,
    region: TravelRegion | None = None,
    activity_type: str | None = None,
    is_active: bool | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[TravelPlace], int]:
    """Truy vấn danh sách địa điểm du lịch kèm bộ lọc, phân trang và tổng số bản ghi."""
    stmt = select(TravelPlace)

    if keyword:
        pattern = f"%{keyword}%"
        stmt = stmt.where(
            or_(
                TravelPlace.name.ilike(pattern),
                TravelPlace.province_city.ilike(pattern),
            )
        )
    if region is not None:
        stmt = stmt.where(TravelPlace.region == region)
    if activity_type:
        stmt = stmt.where(func.lower(TravelPlace.activity_type) == activity_type.lower())
    if is_active is not None:
        stmt = stmt.where(TravelPlace.is_active.is_(is_active))

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = int(db.scalar(count_stmt) or 0)

    items_stmt = stmt.order_by(TravelPlace.id.asc()).offset(offset).limit(limit)
    items = list(db.scalars(items_stmt).all())
    return items, total


def get_travel_place_by_id(db: Session, place_id: int) -> TravelPlace | None:
    """Lấy một địa điểm du lịch theo ID (bao gồm cả trạng thái tạm ngưng)."""
    stmt = select(TravelPlace).where(TravelPlace.id == place_id)
    return db.scalar(stmt)


def get_travel_place_by_name(db: Session, name: str) -> TravelPlace | None:
    """Tìm địa điểm du lịch theo tên (không phân biệt hoa thường) để kiểm tra trùng lặp."""
    stmt = select(TravelPlace).where(func.lower(TravelPlace.name) == name.strip().lower())
    return db.scalar(stmt)


def create_travel_place(db: Session, place_data: dict[str, Any]) -> TravelPlace:
    """Thêm mới địa điểm du lịch vào session và flush để lấy ID/default từ DB."""
    place = TravelPlace(**place_data)
    db.add(place)
    db.flush()
    db.refresh(place)
    return place


def update_travel_place(
    db: Session,
    place: TravelPlace,
    update_data: dict[str, Any],
) -> TravelPlace:
    """Cập nhật các trường của địa điểm du lịch và flush."""
    for field_name, value in update_data.items():
        setattr(place, field_name, value)
    db.flush()
    db.refresh(place)
    return place


def delete_travel_place(db: Session, place: TravelPlace) -> None:
    """Xóa địa điểm du lịch khỏi database và flush."""
    db.delete(place)
    db.flush()
