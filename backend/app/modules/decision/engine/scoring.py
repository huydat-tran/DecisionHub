"""Chuẩn hóa và chấm điểm tiêu chí (Bước 3 - Criteria Scoring) cho Decision Engine.

Module chạy thuần Python trên danh sách ứng viên đã qua bước lọc điều kiện bắt buộc,
không truy vấn database. Hỗ trợ chuẩn hóa Min-Max về thang [0.0, 100.0] cho cả
chiều benefit (max) và cost (min), xử lý trường hợp biên min == max và giữ nguyên
trạng thái thiếu cho dữ liệu bị thiếu (không tự suy diễn điểm).
"""

from collections.abc import Iterable, Sequence
from decimal import Decimal
import math
from typing import Any

# Khi tất cả ứng viên hợp lệ có cùng giá trị (min == max), không có sự phân biệt
# trên tiêu chí đó -> gán điểm tối đa 100.0 để tránh chia cho 0 và không làm giảm
# tổng điểm của tập ứng viên đồng hạng.
EQUAL_RANGE_SCORE: float = 100.0

BENEFIT_DIRECTIONS = frozenset({"max", "benefit"})
COST_DIRECTIONS = frozenset({"min", "cost"})

# Ánh xạ tên tiêu chí trong bảng decision_criteria sang tên trường của ứng viên.
CRITERION_FIELD_MAP: dict[str, str] = {
    "giá": "price",
    "price": "price",
    "mức phù hợp nhu cầu/khẩu vị": "preference",
    "preference": "preference",
    "thời gian chuẩn bị": "prep_time",
    "prep_time": "prep_time",
    "cost": "estimated_cost",
    "duration": "estimated_duration",
    "activities": "activities",
}


def _clamp_score(value: float) -> float:
    """Giới hạn điểm chuẩn hóa trong đoạn [0.0, 100.0]."""
    return max(0.0, min(100.0, value))


def _to_numeric(raw: Any) -> float | None:
    """Chuyển giá trị thô sang float hợp lệ; trả về None nếu thiếu hoặc không hợp lệ."""
    if raw is None or isinstance(raw, bool):
        return None
    if isinstance(raw, (int, float, Decimal)):
        val = float(raw)
        return val if math.isfinite(val) else None
    try:
        val = float(str(raw).strip())
    except (TypeError, ValueError):
        return None
    return val if math.isfinite(val) else None


def _get_field(candidate: Any, field_name: str, default: Any = None) -> Any:
    """Lấy giá trị trường từ dict hoặc object ứng viên."""
    if isinstance(candidate, dict):
        return candidate.get(field_name, default)
    return getattr(candidate, field_name, default)


def _normalize_direction(direction: str) -> str:
    """Chuẩn hóa hướng đánh giá về 'benefit' hoặc 'cost'."""
    cleaned = direction.strip().lower()
    if cleaned in BENEFIT_DIRECTIONS:
        return "benefit"
    if cleaned in COST_DIRECTIONS:
        return "cost"
    raise ValueError(f"Direction không hợp lệ: {direction!r}")


def _resolve_criterion_field(criterion: Any) -> tuple[str, str, float]:
    """Trích xuất (tên_trường, direction, weight) từ object hoặc dict tiêu chí."""
    name = str(_get_field(criterion, "name", "") or "").strip()
    explicit_field = _get_field(criterion, "field_name")
    if explicit_field:
        field_name = str(explicit_field).strip()
    else:
        field_name = CRITERION_FIELD_MAP.get(name.lower(), name)

    direction = str(_get_field(criterion, "direction", "") or "").strip()
    raw_weight = _get_field(criterion, "weight", 0.0)
    weight = _to_numeric(raw_weight)
    if weight is None or weight < 0:
        raise ValueError(f"Weight không hợp lệ cho tiêu chí {name!r}: {raw_weight!r}")

    return field_name, _normalize_direction(direction), weight


def normalize_benefit(value: float, min_val: float, max_val: float) -> float:
    """Chuẩn hóa tiêu chí benefit (càng lớn càng tốt) về thang [0.0, 100.0]."""
    if min_val > max_val:
        raise ValueError(f"min_val ({min_val}) không thể lớn hơn max_val ({max_val})")
    if min_val == max_val:
        return EQUAL_RANGE_SCORE
    return _clamp_score(100.0 * (value - min_val) / (max_val - min_val))


def normalize_cost(value: float, min_val: float, max_val: float) -> float:
    """Chuẩn hóa tiêu chí cost (càng nhỏ càng tốt) về thang [0.0, 100.0]."""
    if min_val > max_val:
        raise ValueError(f"min_val ({min_val}) không thể lớn hơn max_val ({max_val})")
    if min_val == max_val:
        return EQUAL_RANGE_SCORE
    return _clamp_score(100.0 * (max_val - value) / (max_val - min_val))


def normalize_value(
    value: float | int | Decimal | None,
    min_val: float,
    max_val: float,
    direction: str,
) -> float | None:
    """Chuẩn hóa một giá trị đơn lẻ theo direction ('benefit'/'max' hoặc 'cost'/'min').

    Trả về None nếu dữ liệu đầu vào bị thiếu (không tự suy diễn điểm).
    """
    numeric = _to_numeric(value)
    if numeric is None:
        return None

    kind = _normalize_direction(direction)
    if kind == "benefit":
        return normalize_benefit(numeric, min_val, max_val)
    return normalize_cost(numeric, min_val, max_val)


def score_criterion(values: Sequence[Any], direction: str) -> list[float | None]:
    """Chuẩn hóa một dãy giá trị của cùng tiêu chí về thang [0.0, 100.0].

    - Giá trị thiếu/không hợp lệ không tham gia tính min/max và giữ nguyên None.
    - Khi tất cả giá trị hợp lệ bằng nhau (min == max), trả về EQUAL_RANGE_SCORE.
    """
    kind = _normalize_direction(direction)
    parsed = [_to_numeric(v) for v in values]
    valid_values = [v for v in parsed if v is not None]

    if not valid_values:
        return [None for _ in parsed]

    min_val = min(valid_values)
    max_val = max(valid_values)

    normalizer = normalize_benefit if kind == "benefit" else normalize_cost
    return [None if v is None else normalizer(v, min_val, max_val) for v in parsed]


def score_candidates(
    candidates: Iterable[Any],
    criteria: Sequence[Any],
) -> list[dict[str, Any]]:
    """Chuẩn hóa điểm từng tiêu chí (0-100) cho danh sách ứng viên.

    Trả về danh sách dict với trường `criteria_scores` chứa điểm đã chuẩn hóa.
    Không tính tổng WSM — việc đó thuộc về calculator.py.

    Quy tắc xử lý dữ liệu thiếu:
    - Không tự suy diễn điểm cho trường bị thiếu: `criteria_scores[field]` là None.
    """
    candidate_list = list(candidates)
    if not candidate_list:
        return []

    resolved_criteria = [_resolve_criterion_field(c) for c in criteria]

    # Chuẩn hóa từng tiêu chí trên toàn bộ tập ứng viên
    per_criterion_scores: dict[str, list[float | None]] = {}
    for field_name, direction, _weight in resolved_criteria:
        raw_values = [_get_field(cand, field_name) for cand in candidate_list]
        per_criterion_scores[field_name] = score_criterion(raw_values, direction)

    results: list[dict[str, Any]] = []
    for idx, cand in enumerate(candidate_list):
        base = dict(cand) if isinstance(cand, dict) else {"item": cand}
        criteria_scores: dict[str, float | None] = {}

        for field_name, _direction, _weight in resolved_criteria:
            c_score = per_criterion_scores[field_name][idx]
            criteria_scores[field_name] = round(c_score, 2) if c_score is not None else None

        base["criteria_scores"] = criteria_scores
        results.append(base)

    return results
