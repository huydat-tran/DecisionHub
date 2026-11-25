"""Định danh chuẩn của tiêu chí quyết định (`field_name`).

Đây là nguồn định nghĩa duy nhất cho ánh xạ giữa `decision_criteria.name`
(tên hiển thị trong DB, ví dụ "Giá") và `field_name` — định danh kỹ thuật mà
Decision Engine dùng làm key tính toán (trọng số, `criteria_scores`).

Quy ước: mọi dữ liệu đi vào Decision Engine đều dùng `field_name`.
Tên hiển thị vẫn được dùng ở DB và giao diện, nhưng không dùng làm key tính toán.

Ví dụ:
    "Giá"                      -> "price"
    "Thời gian chuẩn bị"       -> "prep_time"
    "cost"                     -> "estimated_cost"
    "duration"                 -> "estimated_duration"
"""

from typing import Any

# Tên tiêu chí trong DB (đã lowercase) -> field_name chuẩn của Engine.
# Mỗi field_name chuẩn cũng tự ánh xạ về chính nó để dữ liệu đã chuẩn hóa
# đi qua hàm ánh xạ là idempotent.
CRITERION_FIELD_MAP: dict[str, str] = {
    "giá": "price",
    "price": "price",
    "mức phù hợp nhu cầu/khẩu vị": "preference",
    "preference": "preference",
    "thời gian chuẩn bị": "prep_time",
    "prep_time": "prep_time",
    "cost": "estimated_cost",
    "estimated_cost": "estimated_cost",
    "chi phí": "estimated_cost",
    "duration": "estimated_duration",
    "estimated_duration": "estimated_duration",
    "thời lượng": "estimated_duration",
    "activities": "activities",
    "hoạt động": "activities",
}

# Tập field_name hợp lệ — chặn key sai (vd. "Giá") đi vào Engine.
CANONICAL_FIELD_NAMES: frozenset[str] = frozenset(CRITERION_FIELD_MAP.values())


def _get_field(source: Any, field_name: str) -> Any:
    """Lấy giá trị trường từ dict hoặc object."""
    if isinstance(source, dict):
        return source.get(field_name)
    return getattr(source, field_name, None)


def resolve_field_name(name: str) -> str:
    """Ánh xạ tên tiêu chí sang `field_name` chuẩn.

    Hàm này là idempotent: truyền vào một `field_name` đã chuẩn hóa sẽ trả về
    chính giá trị đó.

    Args:
        name: Tên tiêu chí trong DB hoặc `field_name` đã chuẩn hóa.

    Returns:
        field_name chuẩn.

    Raises:
        ValueError: Khi không tìm được ánh xạ cho tên tiêu chí.
    """
    key = (name or "").strip().lower()
    field_name = CRITERION_FIELD_MAP.get(key)
    if field_name is None:
        raise ValueError(
            f"Không tìm thấy ánh xạ field_name cho tiêu chí {name!r}. "
            f"Các field_name hợp lệ: {sorted(CANONICAL_FIELD_NAMES)}."
        )
    return field_name


def resolve_criterion_field(criterion: Any) -> str:
    """Lấy `field_name` chuẩn từ một tiêu chí (dict hoặc object).

    Ưu tiên `field_name` nếu tiêu chí đã có sẵn trường này, ngược lại ánh xạ từ
    `name`. Dùng chung cho cả Scoring và Calculator để hai tầng luôn gắn trọng
    số với đúng điểm của tiêu chí tương ứng.

    Raises:
        ValueError: Khi tiêu chí không ánh xạ được về field_name hợp lệ.
    """
    explicit = _get_field(criterion, "field_name")
    if explicit:
        field_name = str(explicit).strip()
        if field_name not in CANONICAL_FIELD_NAMES:
            raise ValueError(
                f"field_name {field_name!r} không hợp lệ. "
                f"Các field_name hợp lệ: {sorted(CANONICAL_FIELD_NAMES)}."
            )
        return field_name

    return resolve_field_name(str(_get_field(criterion, "name") or ""))
