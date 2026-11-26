"""Adapter chuyển đổi Travel candidates và criteria sang cấu trúc chung của Decision Engine.

Đảm bảo tuân thủ kiến trúc DecisionHub:
- Decision Engine nhận dữ liệu đã chuẩn hóa, không phụ thuộc database và không chứa domain logic.
- Module Travel chịu trách nhiệm chuyển đổi dữ liệu đặc thù của địa điểm du lịch sang format chung.
"""

import math
from collections.abc import Iterable, Sequence
from enum import Enum
from typing import Any

from app.modules.decision.criterion_fields import (
    resolve_criterion_field,
    resolve_field_name,
)
from app.modules.decision.engine._utils import _get_field
from app.modules.decision.engine.calculator import validate_weights

WEIGHT_SUM_TOLERANCE: float = 1e-6

DEFAULT_TRAVEL_WEIGHTS: dict[str, float] = {
    "estimated_cost": 0.40,
    "estimated_duration": 0.30,
    "activities": 0.30,
}

DEFAULT_TRAVEL_CRITERIA: list[dict[str, Any]] = [
    {
        "domain": "travel",
        "name": "cost",
        "field_name": "estimated_cost",
        "direction": "min",
        "weight": 0.40,
    },
    {
        "domain": "travel",
        "name": "duration",
        "field_name": "estimated_duration",
        "direction": "min",
        "weight": 0.30,
    },
    {
        "domain": "travel",
        "name": "activities",
        "field_name": "activities",
        "direction": "max",
        "weight": 0.30,
    },
]


def _extract_highlights(candidate: Any) -> list[str]:
    """Trích xuất danh sách hoạt động nổi bật từ chuỗi, list hoặc property."""
    highlights_list = _get_field(candidate, "highlights_list")
    if isinstance(highlights_list, list):
        return [str(h).strip() for h in highlights_list if str(h).strip()]

    raw = _get_field(candidate, "highlights")
    if isinstance(raw, list):
        return [str(h).strip() for h in raw if str(h).strip()]
    if isinstance(raw, str) and raw.strip():
        return [h.strip() for h in raw.replace("\n", ",").split(",") if h.strip()]
    return []


def _extract_activities_count(candidate: Any, highlights: list[str]) -> float:
    """Tính số lượng hoạt động nổi bật phục vụ tiêu chí 'activities'."""
    raw = _get_field(candidate, "activities")
    if raw is not None and not isinstance(raw, bool):
        try:
            val = float(raw)
            if math.isfinite(val):
                return val
        except (TypeError, ValueError):
            pass
        if isinstance(raw, (list, tuple, set)):
            return float(len(raw))
    return float(len(highlights))


def adapt_travel_candidate(
    candidate: Any,
    preferred_activities: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Chuyển đổi một ứng viên Travel (ORM, Pydantic, dict) sang cấu trúc chung của Decision Engine.

    Output format phẳng:
    - id / destination_id: int
    - name: str
    - estimated_cost: int (chi phí VND, phục vụ tie-break và tiêu chí cost)
    - estimated_duration: float (thời lượng giờ, phục vụ tiêu chí duration)
    - activities: float (số lượng hoạt động, phục vụ tiêu chí activities)
    - activity_type: str
    - region: str
    - province_city: str
    - highlights: list[str]
    - tags: list[str]
    - matched_activities: list[str]
    - description: str | None
    - image_url: str | None
    - rating: float | None
    - item: object gốc
    """
    cand_id = _get_field(candidate, "id") or _get_field(candidate, "destination_id") or 0
    try:
        cand_id = int(cand_id)
    except (TypeError, ValueError):
        cand_id = 0

    name = str(_get_field(candidate, "name") or "")

    # Chi phí: ưu tiên estimated_cost, fallback sang cost hoặc price
    raw_cost = (
        _get_field(candidate, "estimated_cost")
        if _get_field(candidate, "estimated_cost") is not None
        else _get_field(candidate, "cost")
        if _get_field(candidate, "cost") is not None
        else _get_field(candidate, "price")
    )
    try:
        estimated_cost = int(float(raw_cost)) if raw_cost is not None else 0
    except (TypeError, ValueError):
        estimated_cost = 0

    # Thời lượng: ưu tiên estimated_duration, fallback sang duration
    raw_duration = (
        _get_field(candidate, "estimated_duration")
        if _get_field(candidate, "estimated_duration") is not None
        else _get_field(candidate, "duration")
    )
    try:
        estimated_duration = float(raw_duration) if raw_duration is not None else 0.0
    except (TypeError, ValueError):
        estimated_duration = 0.0

    highlights = _extract_highlights(candidate)
    base_activities_count = _extract_activities_count(candidate, highlights)

    matched_activities: list[str] = []
    activities_count = base_activities_count
    if preferred_activities:
        pref_lower = [str(p).strip().lower() for p in preferred_activities if str(p).strip()]
        for h in highlights:
            h_lower = h.lower()
            if any(p in h_lower for p in pref_lower):
                matched_activities.append(h)
        act_type_raw = str(_get_field(candidate, "activity_type") or "").strip()
        if (
            act_type_raw
            and any(p in act_type_raw.lower() for p in pref_lower)
            and act_type_raw not in matched_activities
        ):
            matched_activities.append(act_type_raw)
        if matched_activities:
            activities_count += len(matched_activities) * 5.0

    tags = list(highlights)
    act_type = str(_get_field(candidate, "activity_type") or "").strip()
    if act_type and act_type not in tags:
        tags.append(act_type)

    region_raw = _get_field(candidate, "region")
    region_str = region_raw.value if isinstance(region_raw, Enum) else str(region_raw or "")

    rating_raw = _get_field(candidate, "rating")
    rating_val: float | None = None
    if rating_raw is not None:
        try:
            rating_val = float(rating_raw)
        except (TypeError, ValueError):
            rating_val = None

    return {
        "id": cand_id,
        "destination_id": cand_id,
        "name": name,
        "estimated_cost": estimated_cost,
        "estimated_duration": estimated_duration,
        "activities": activities_count,
        "activity_type": str(_get_field(candidate, "activity_type") or ""),
        "region": region_str,
        "province_city": str(_get_field(candidate, "province_city") or ""),
        "highlights": highlights,
        "tags": tags,
        "matched_activities": matched_activities,
        "description": _get_field(candidate, "description"),
        "image_url": _get_field(candidate, "image_url"),
        "rating": rating_val,
        "item": candidate,
    }


def adapt_travel_candidates(
    candidates: Iterable[Any],
    preferred_activities: Sequence[str] | None = None,
) -> list[dict[str, Any]]:
    """Chuyển đổi danh sách ứng viên Travel sang cấu trúc chung của Decision Engine."""
    return [adapt_travel_candidate(c, preferred_activities=preferred_activities) for c in (candidates or [])]


def _normalize_custom_weights(custom_weights: dict[str, float]) -> dict[str, float]:
    """Chuẩn hóa key của custom_weights sang canonical field_name và validate tổng."""
    normalized: dict[str, float] = {}
    for raw_key, raw_weight in custom_weights.items():
        canonical_key = resolve_field_name(str(raw_key))
        try:
            w_val = float(raw_weight)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Trọng số cho {raw_key!r} phải là số thực.") from exc
        if not math.isfinite(w_val) or w_val < 0 or w_val > 1:
            raise ValueError(f"Trọng số {w_val} của {raw_key!r} phải nằm trong đoạn [0, 1].")
        normalized[canonical_key] = w_val

    total = sum(normalized.values())
    if not math.isclose(total, 1.0, abs_tol=WEIGHT_SUM_TOLERANCE):
        raise ValueError(f"Tổng trọng số tùy chỉnh phải bằng 1.0 (hiện tại: {total:.4f}).")

    return normalized


def adapt_travel_criteria(
    criteria: Sequence[Any] | None = None,
    custom_weights: dict[str, float] | None = None,
) -> list[dict[str, Any]]:
    """Chuyển đổi danh sách tiêu chí Travel sang cấu trúc chung của Decision Engine.

    - Nếu `criteria` rỗng hoặc None: sử dụng `DEFAULT_TRAVEL_CRITERIA`.
    - Chuẩn hóa tên tiêu chí về `field_name` chuẩn qua `resolve_criterion_field`.
    - Hỗ trợ ghi đè trọng số bằng `custom_weights` (tổng trọng số phải bằng 1.0).
    """
    normalized_weights = _normalize_custom_weights(custom_weights) if custom_weights else None

    if not criteria:
        adapted = [dict(c) for c in DEFAULT_TRAVEL_CRITERIA]
    else:
        adapted = []
        for c in criteria:
            if isinstance(c, dict):
                crit_dict = {
                    "domain": c.get("domain", "travel"),
                    "name": c.get("name", ""),
                    "field_name": resolve_criterion_field(c),
                    "direction": c.get("direction", "min"),
                    "weight": float(c.get("weight", 0.0)),
                }
            else:
                crit_dict = {
                    "domain": getattr(c, "domain", "travel"),
                    "name": getattr(c, "name", ""),
                    "field_name": resolve_criterion_field(c),
                    "direction": getattr(c, "direction", "min"),
                    "weight": float(getattr(c, "weight", 0.0)),
                }
            adapted.append(crit_dict)

    if normalized_weights:
        for c in adapted:
            fn = c.get("field_name")
            if fn in normalized_weights:
                c["weight"] = normalized_weights[fn]

    # Kiểm tra tính hợp lệ của trọng số theo quy chuẩn WSM
    validate_weights(adapted)

    return adapted
