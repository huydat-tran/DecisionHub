"""Repository cho module Travel – truy vấn database travel_places.

Tuân thủ luồng: router → service → repository → MySQL.
Repository chỉ chứa logic truy vấn; không có business logic.
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.modules.travel.models import TravelPlace


def get_active_places(db: Session) -> list[TravelPlace]:
    """Lấy toàn bộ địa điểm đang hoạt động (is_active=True).

    Dùng cho Candidate Retrieval trong Decision Engine (UC03).
    """
    return db.query(TravelPlace).filter(TravelPlace.is_active.is_(True)).all()


def get_place_by_id(db: Session, place_id: int) -> TravelPlace | None:
    """Lấy địa điểm theo ID. Trả về None nếu không tồn tại."""
    return db.query(TravelPlace).filter(TravelPlace.id == place_id).first()


def search_places(
    db: Session,
    keyword: str | None = None,
    region: str | None = None,
    budget_max: int | None = None,
    max_duration: float | None = None,
    activity_type: str | None = None,
    limit: int = 20,
) -> list[TravelPlace]:
    """Tìm kiếm địa điểm theo keyword và bộ lọc chip nhanh (UC01 Quick Search).

    Args:
        db: Database session.
        keyword: Từ khóa tìm trong name, province_city, description.
        region: Lọc theo khu vực (Bắc, Trung, Nam, Tây Nguyên, Tây Nam Bộ).
        budget_max: Lọc theo ngân sách tối đa (VND).
        max_duration: Lọc theo thời lượng tối đa (giờ).
        activity_type: Lọc theo loại hình trải nghiệm.
        limit: Số kết quả tối đa. Mặc định 20.

    Returns:
        Danh sách TravelPlace khớp điều kiện.
    """
    query = db.query(TravelPlace).filter(TravelPlace.is_active.is_(True))

    if keyword:
        kw = f"%{keyword}%"
        query = query.filter(
            TravelPlace.name.ilike(kw)
            | TravelPlace.province_city.ilike(kw)
            | TravelPlace.description.ilike(kw)
        )

    if region:
        query = query.filter(TravelPlace.region == region)

    if budget_max is not None:
        query = query.filter(TravelPlace.estimated_cost <= budget_max)

    if max_duration is not None:
        query = query.filter(TravelPlace.estimated_duration <= Decimal(str(max_duration)))

    if activity_type:
        query = query.filter(TravelPlace.activity_type == activity_type)

    return query.order_by(TravelPlace.rating.desc()).limit(limit).all()
