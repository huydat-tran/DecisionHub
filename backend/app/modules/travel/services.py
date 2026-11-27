"""Dịch vụ nghiệp vụ cho module Travel (CRUD quản trị & đóng gói kết quả gợi ý)."""

from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.common.exceptions import (
    BadRequestException,
    DecisionHubException,
    ResourceNotFoundException,
)
from app.modules.travel.models import TravelPlace, TravelRegion
from app.modules.travel.repository import (
    create_travel_place,
    delete_travel_place,
    get_travel_place_by_id,
    get_travel_place_by_name,
    list_travel_places,
    update_travel_place,
)
from app.modules.travel.schemas import (
    RecommendedTravelResponse,
    TravelAppliedFilters,
    TravelDecisionData,
    TravelExcludedOptionResponse,
    TravelPlaceCreateRequest,
    TravelPlaceDeleteData,
    TravelPlaceListData,
    TravelPlaceOut,
    TravelPlaceUpdateRequest,
    TravelRecommendRequest,
    TravelScoringResponse,
)


def _format_vnd(amount: int) -> str:
    """Format số tiền VND sang định dạng hiển thị (vd: 500000 -> '500.000đ')."""
    return f"{amount:,}".replace(",", ".") + "đ"


def _build_travel_reasons(
    cand: dict[str, Any],
    payload: TravelRecommendRequest,
) -> list[str]:
    """Sinh 1-3 lý do gợi ý dựa trên dữ liệu thực tế và điều kiện đầu vào của người dùng."""
    reasons: list[str] = []
    cost = int(cand.get("estimated_cost", 0))
    duration = float(cand.get("estimated_duration", 0.0))

    # 1. Lý do Chi phí
    if cost == 0:
        reasons.append("Chi phí 0đ, tối ưu ngân sách")
    elif payload.budget_max is not None:
        reasons.append(
            f"Chi phí {_format_vnd(cost)} nằm trong ngân sách tối đa {_format_vnd(payload.budget_max)}"
        )
    else:
        reasons.append(f"Chi phí tham khảo: {_format_vnd(cost)}")

    # 2. Lý do Thời lượng
    if payload.max_duration is not None:
        reasons.append(
            f"Thời lượng {duration:.1f}h phù hợp giới hạn {payload.max_duration:.1f}h"
        )
    else:
        reasons.append(f"Thời lượng trải nghiệm ước tính: {duration:.1f}h")

    # 3. Lý do Hoạt động / Sở thích
    matched = cand.get("matched_activities") or []
    if matched:
        reasons.append(f"Phù hợp sở thích / hoạt động: {', '.join(matched[:3])}")
    elif cand.get("highlights"):
        reasons.append(f"Có {len(cand['highlights'])} hoạt động trải nghiệm nổi bật")
    elif cand.get("activity_type"):
        reasons.append(f"Loại hình trải nghiệm: {cand['activity_type']}")

    return reasons[:3]


def build_travel_decision_response(
    ranked_candidates: list[dict[str, Any]],
    total_valid: int,
    excluded_items: list[TravelExcludedOptionResponse],
    adapted_criteria: list[dict[str, Any]],
    payload: TravelRecommendRequest,
) -> tuple[TravelDecisionData, str]:
    """Đóng gói kết quả gợi ý thành dữ liệu hiển thị TravelDecisionData và thông báo."""
    items: list[RecommendedTravelResponse] = []
    for cand in ranked_candidates:
        reasons = _build_travel_reasons(cand, payload)
        dest_id = int(cand.get("destination_id") or cand.get("id") or 0)
        items.append(
            RecommendedTravelResponse(
                destination_id=dest_id,
                name=str(cand.get("name") or ""),
                province_city=str(cand.get("province_city") or ""),
                region=str(cand.get("region") or ""),
                estimated_cost=int(cand.get("estimated_cost") or 0),
                estimated_duration=float(cand.get("estimated_duration") or 0.0),
                activity_type=str(cand.get("activity_type") or ""),
                highlights=list(cand.get("highlights") or []),
                description=cand.get("description"),
                image_url=cand.get("image_url"),
                rating=cand.get("rating"),
                score=float(cand.get("score") or 0.0),
                total_score=float(cand.get("total_score") or cand.get("score") or 0.0),
                rank=int(cand.get("rank") or 1),
                criteria_scores=dict(cand.get("criteria_scores") or {}),
                criteria_details=dict(cand.get("criteria_details") or {}),
                reasons=reasons,
                id=dest_id,
            )
        )

    weights_dict = {c["field_name"]: c["weight"] for c in adapted_criteria}
    region_str = payload.region.value if payload.region is not None else None
    decision_data = TravelDecisionData(
        items=items,
        excluded_items=excluded_items,
        total=total_valid,
        total_excluded=len(excluded_items),
        limit=payload.limit,
        applied_filters=TravelAppliedFilters(
            budget_max=payload.budget_max,
            max_duration=payload.max_duration,
            region=region_str,
            activity_type=payload.activity_type,
            preferred_activities=payload.preferred_activities,
        ),
        scoring=TravelScoringResponse(
            method="WSM",
            weights=weights_dict,
        ),
    )

    if not items:
        message = (
            "Không có địa điểm nào thỏa mãn toàn bộ điều kiện. "
            "Hãy thử tăng ngân sách tối đa hoặc nới thời lượng."
        )
    else:
        message = f"Đề xuất {len(items)} địa điểm du lịch phù hợp nhất."

    return decision_data, message


def _serialize_highlights(highlights: list[str] | None) -> str | None:
    """Chuyển danh sách highlights đã chuẩn hóa sang chuỗi lưu DB."""
    if not highlights:
        return None
    return ", ".join(highlights)


def _to_travel_place_out(place: TravelPlace) -> TravelPlaceOut:
    """Chuyển ORM TravelPlace sang schema response chuẩn."""
    return TravelPlaceOut.model_validate(place)


def _require_travel_place(db: Session, place_id: int) -> TravelPlace:
    """Lấy địa điểm theo ID hoặc ném ResourceNotFoundException (404)."""
    place = get_travel_place_by_id(db, place_id)
    if place is None:
        raise ResourceNotFoundException("Địa điểm du lịch", place_id)
    return place


def _ensure_unique_place_name(
    db: Session,
    name: str,
    *,
    exclude_place_id: int | None = None,
) -> None:
    """Kiểm tra tên địa điểm chưa bị trùng; nếu trùng ném lỗi 409 CONFLICT."""
    existing = get_travel_place_by_name(db, name)
    if existing is not None and existing.id != exclude_place_id:
        raise DecisionHubException(
            message=f"Địa điểm '{name}' đã tồn tại.",
            status_code=409,
        )


def _build_place_payload_dict(payload: TravelPlaceCreateRequest) -> dict[str, Any]:
    """Chuyển dữ liệu đã validate từ TravelPlaceCreateRequest sang dict ghi DB."""
    return {
        "name": payload.name,
        "province_city": payload.province_city,
        "region": payload.region,
        "estimated_cost": payload.estimated_cost,
        "estimated_duration": payload.estimated_duration,
        "activity_type": payload.activity_type,
        "highlights": _serialize_highlights(payload.highlights),
        "description": payload.description,
        "image_url": payload.image_url,
        "rating": payload.rating,
        "is_active": payload.is_active,
    }


def list_admin_travel_places(
    db: Session,
    *,
    keyword: str | None = None,
    region: TravelRegion | None = None,
    activity_type: str | None = None,
    is_active: bool | None = None,
    limit: int = 20,
    offset: int = 0,
) -> TravelPlaceListData:
    """Lấy danh sách địa điểm du lịch cho quản trị viên (kèm tìm kiếm, lọc và phân trang)."""
    clean_keyword = keyword.strip() if keyword and keyword.strip() else None
    clean_activity = activity_type.strip() if activity_type and activity_type.strip() else None

    places, total = list_travel_places(
        db,
        keyword=clean_keyword,
        region=region,
        activity_type=clean_activity,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )
    return TravelPlaceListData(
        items=[_to_travel_place_out(place) for place in places],
        total=total,
        limit=limit,
        offset=offset,
    )


def get_admin_travel_place_detail(db: Session, place_id: int) -> TravelPlaceOut:
    """Lấy chi tiết một địa điểm du lịch theo ID."""
    place = _require_travel_place(db, place_id)
    return _to_travel_place_out(place)


def create_admin_travel_place(
    db: Session,
    payload: TravelPlaceCreateRequest,
) -> TravelPlaceOut:
    """Tạo mới địa điểm du lịch sau khi kiểm tra trùng tên."""
    _ensure_unique_place_name(db, payload.name)
    place_data = _build_place_payload_dict(payload)
    try:
        place = create_travel_place(db, place_data)
        db.commit()
        db.refresh(place)
    except IntegrityError:
        db.rollback()
        raise DecisionHubException(
            message=f"Địa điểm '{payload.name}' đã tồn tại.",
            status_code=409,
        ) from None
    except Exception:
        db.rollback()
        raise
    return _to_travel_place_out(place)


def replace_admin_travel_place(
    db: Session,
    place_id: int,
    payload: TravelPlaceCreateRequest,
) -> TravelPlaceOut:
    """Cập nhật toàn bộ thông tin địa điểm du lịch theo ID (PUT)."""
    place = _require_travel_place(db, place_id)
    _ensure_unique_place_name(db, payload.name, exclude_place_id=place.id)
    update_data = _build_place_payload_dict(payload)
    try:
        updated = update_travel_place(db, place, update_data)
        db.commit()
        db.refresh(updated)
    except IntegrityError:
        db.rollback()
        raise DecisionHubException(
            message=f"Địa điểm '{payload.name}' đã tồn tại.",
            status_code=409,
        ) from None
    except Exception:
        db.rollback()
        raise
    return _to_travel_place_out(updated)


def update_admin_travel_place(
    db: Session,
    place_id: int,
    payload: TravelPlaceUpdateRequest,
) -> TravelPlaceOut:
    """Cập nhật một phần thông tin địa điểm du lịch theo ID (PATCH)."""
    place = _require_travel_place(db, place_id)
    fields_set = payload.model_fields_set
    if not fields_set:
        raise BadRequestException("Không có trường nào được cập nhật.")

    if "name" in fields_set and payload.name is not None:
        _ensure_unique_place_name(db, payload.name, exclude_place_id=place.id)

    update_data: dict[str, Any] = {}
    for field_name in fields_set:
        if field_name == "highlights":
            update_data["highlights"] = _serialize_highlights(payload.highlights)
        else:
            update_data[field_name] = getattr(payload, field_name)

    try:
        updated = update_travel_place(db, place, update_data)
        db.commit()
        db.refresh(updated)
    except IntegrityError:
        db.rollback()
        raise DecisionHubException(
            message=f"Địa điểm '{payload.name or place.name}' đã tồn tại.",
            status_code=409,
        ) from None
    except Exception:
        db.rollback()
        raise
    return _to_travel_place_out(updated)


def delete_admin_travel_place(db: Session, place_id: int) -> TravelPlaceDeleteData:
    """Xóa địa điểm du lịch theo ID."""
    place = _require_travel_place(db, place_id)
    deleted = TravelPlaceDeleteData(id=place.id, name=place.name)
    try:
        delete_travel_place(db, place)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise DecisionHubException(
            message="Không thể xóa địa điểm vì đang được dữ liệu khác tham chiếu.",
            status_code=409,
        ) from None
    except Exception:
        db.rollback()
        raise
    return deleted
