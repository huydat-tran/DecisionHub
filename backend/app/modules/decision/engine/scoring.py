"""Chuẩn hóa và chấm điểm tiêu chí (Bước 3 - Criteria Scoring) cho Decision Engine.

Module chạy thuần Python trên danh sách ứng viên đã qua bước lọc điều kiện bắt buộc,
không truy vấn database. Hỗ trợ chuẩn hóa Min-Max về thang [0.0, 100.0] cho cả
chiều benefit (max) và cost (min), xử lý trường hợp biên min == max và giữ nguyên
trạng thái thiếu cho dữ liệu bị thiếu (không tự suy diễn điểm).

Ứng viên được chuẩn hóa về dict phẳng trước khi chấm điểm, để Ranking đọc được
`id`/`name`/`price`... ở cấp ngoài cùng (xem `_to_candidate_dict`).

Tiêu chí `preference` được chấm riêng theo cơ chế khớp tag (không dùng Min-Max):
`score_preference()` trả điểm trong [0.0, 1.0], được quy đổi ×100 để đồng bộ
thang điểm của các tiêu chí khác trước khi đưa vào WSM.
"""

from collections.abc import Iterable, Sequence
from decimal import Decimal
import math
from typing import Any

from app.modules.decision.criterion_fields import resolve_criterion_field

# Khi tất cả ứng viên hợp lệ có cùng giá trị (min == max), không có sự phân biệt
# trên tiêu chí đó -> gán điểm tối đa 100.0 để tránh chia cho 0 và không làm giảm
# tổng điểm của tập ứng viên đồng hạng.
EQUAL_RANGE_SCORE: float = 100.0

BENEFIT_DIRECTIONS = frozenset({"max", "benefit"})
COST_DIRECTIONS = frozenset({"min", "cost"})

# `field_name` chuẩn của tiêu chí sở thích trong criteria_scores.
PREFERENCE_FIELD: str = "preference"

# Field của ứng viên chứa danh sách tag (vd. cột JSON `foods.tags`).
CANDIDATE_TAGS_FIELD: str = "tags"

# Điểm trung tính khi người dùng không nêu sở thích: không ưu tiên ứng viên nào
# nhưng vẫn giữ tiêu chí `preference` tham gia WSM với trọng số hiện có.
NEUTRAL_PREFERENCE_SCORE: float = 0.5


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


from ._utils import _get_field


def _to_candidate_dict(candidate: Any) -> dict[str, Any]:
    """Chuẩn hóa ứng viên về dict phẳng để Ranking đọc được ở cấp ngoài cùng.

    Hỗ trợ 3 kiểu dữ liệu thực tế của dự án:
    - dict: sao chép nông, giữ nguyên cấu trúc.
    - Pydantic v2 model: lấy các field đã khai báo.
    - SQLAlchemy ORM object: chỉ lấy cột đã load (không đụng relationship/lazy load).

    Ứng viên gốc luôn được giữ ở trường `item` để tầng trên vẫn truy cập được
    object gốc (ví dụ để đọc relationship `ingredients` khi sinh lý do gợi ý).
    """
    if isinstance(candidate, dict):
        # Dict đã phẳng sẵn → sao chép nông, không cần trường `item`.
        return dict(candidate)

    # Pydantic v2: lấy đúng các field đã khai báo trong model.
    model_fields = getattr(type(candidate), "model_fields", None)
    # SQLAlchemy ORM: chỉ lấy cột đã load trong __dict__ (bỏ relationship
    # để không kích hoạt truy vấn ngoài ý muốn).
    mapper = getattr(type(candidate), "__mapper__", None)
    if model_fields is not None:
        out: dict[str, Any] = {name: getattr(candidate, name) for name in model_fields}
    elif mapper is not None:
        loaded = getattr(candidate, "__dict__", None) or {}
        out = {
            key: loaded[key]
            for key in mapper.column_attrs.keys()
            if key in loaded
        }
    else:
        # Object thuần: chỉ lấy thuộc tính công khai (bỏ thuộc tính nội bộ).
        state = getattr(candidate, "__dict__", None) or {}
        out = {k: v for k, v in state.items() if not k.startswith("_")}

    # Giữ ứng viên gốc để tầng trên vẫn đọc được object gốc
    # (ví dụ để lấy relationship `ingredients` khi sinh lý do gợi ý).
    out["item"] = candidate
    return out


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
    # field_name chuẩn dùng chung với Calculator (nguồn định nghĩa duy nhất).
    field_name = resolve_criterion_field(criterion)

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


def _normalize_tags(raw: Any) -> set[str]:
    """Chuẩn hóa danh sách tag thành set chữ thường, đã bỏ khoảng trắng và rỗng.

    Hỗ trợ list/tuple/set các chuỗi và chuỗi phân tách bằng dấu phẩy (dạng cột
    JSON lưu "spicy,vegan"). Kiểu dữ liệu khác được coi là không có tag.
    """
    if raw is None:
        return set()
    if isinstance(raw, str):
        items: list[Any] = raw.split(",")
    elif isinstance(raw, (list, tuple, set, frozenset)):
        items = list(raw)
    else:
        return set()

    tags: set[str] = set()
    for item in items:
        if item is None:
            continue
        cleaned = str(item).strip().lower()
        if cleaned:
            tags.add(cleaned)
    return tags


def score_preference(candidate_tags: Any, user_preferences: Any) -> float:
    """Tính điểm phù hợp sở thích của một ứng viên trong khoảng [0, 1].

    Công thức: `số sở thích khớp / tổng số sở thích người dùng cung cấp`.

    - So sánh tag không phân biệt hoa/thường và bỏ khoảng trắng thừa.
    - Tag trùng lặp chỉ được tính một lần; khớp theo đúng phần tử (không so
      khớp substring để tránh nhầm các tag khác nhau).
    - Ứng viên không có tag → 0.0 (vẫn còn sở thích để đối chiếu).
    - Người dùng không nêu sở thích → điểm trung tính NEUTRAL_PREFERENCE_SCORE,
      không ưu tiên ứng viên nào và không làm sai lệch thứ hạng.
    """
    user_tags = _normalize_tags(user_preferences)
    if not user_tags:
        return NEUTRAL_PREFERENCE_SCORE

    food_tags = _normalize_tags(candidate_tags)
    if not food_tags:
        return 0.0

    matched = len(user_tags & food_tags)
    return matched / len(user_tags)


def score_candidates(
    candidates: Iterable[Any],
    criteria: Sequence[Any],
    user_preferences: Sequence[str] | None = None,
) -> list[dict[str, Any]]:
    """Chuẩn hóa điểm từng tiêu chí (0-100) cho danh sách ứng viên.

    Trả về danh sách dict với trường `criteria_scores` chứa điểm đã chuẩn hóa.
    Không tính tổng WSM — việc đó thuộc về calculator.py.

    Ứng viên dict/Pydantic/ORM đều được chuẩn hóa về dict phẳng, các trường cần
    cho Ranking (id/name/price...) nằm ở cấp ngoài cùng; ứng viên gốc được giữ
    ở trường `item`.

    Args:
        candidates: Danh sách ứng viên.
        criteria: Danh sách tiêu chí (có `name`/`field_name`, `direction`, `weight`).
        user_preferences: Sở thích (tag) của người dùng.
            - `None` (mặc định): không có thông tin sở thích → tiêu chí
              `preference` dùng Min-Max trên field `preference` sẵn có của ứng viên
              (hành vi cũ, giữ nguyên cho caller cũ).
            - Danh sách (kể cả rỗng): tiêu chí `preference` được chấm bằng cơ chế
              khớp tag (`score_preference`), quy đổi ×100 để đồng bộ thang điểm
              0-100 của các tiêu chí khác. Danh sách rỗng → mọi ứng viên cùng
              nhận điểm trung tính 50.0.

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
        if field_name == PREFERENCE_FIELD and user_preferences is not None:
            # Tiêu chí sở thích dùng cơ chế khớp tag thay cho Min-Max.
            per_criterion_scores[field_name] = [
                100.0
                * score_preference(
                    _get_field(cand, CANDIDATE_TAGS_FIELD),
                    user_preferences,
                )
                for cand in candidate_list
            ]
            continue

        raw_values = [_get_field(cand, field_name) for cand in candidate_list]
        per_criterion_scores[field_name] = score_criterion(raw_values, direction)

    results: list[dict[str, Any]] = []
    for idx, cand in enumerate(candidate_list):
        base = _to_candidate_dict(cand)
        criteria_scores: dict[str, float | None] = {}

        for field_name, _direction, _weight in resolved_criteria:
            c_score = per_criterion_scores[field_name][idx]
            criteria_scores[field_name] = round(c_score, 2) if c_score is not None else None

        base["criteria_scores"] = criteria_scores
        results.append(base)

    return results
