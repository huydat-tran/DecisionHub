"""Bộ lọc điều kiện bắt buộc (Hard Constraints) cho Decision Engine.

Module này chạy thuần Python trên danh sách ứng viên đã chuẩn hóa,
không truy vấn database. Vi phạm bất kỳ điều kiện bắt buộc nào
ứng viên sẽ bị loại ngay trước khi chấm điểm WSM.

Cấu hình điều kiện đến từ tầng ngoài (Service) dưới dạng dict:

    {
        "price": ("<=", 100000),
        "meal_type": ("=", "lunch"),
        "prep_time": ("<=", 30),
        "ingredients": ("not_in", ["peanut", "shrimp"]),
    }

Key là `field_name` của ứng viên, value là cặp `(operator, giá trị)`.
Toán tử được hỗ trợ: `<=`, `>=`, `=`, `!=`, `in`, `not_in`.

Cấu hình field/operator được tra theo domain từ `hard_constraint_fields.py`;
cơ chế so sánh và dispatch operator là dùng chung cho mọi domain.
"""

import math
from collections.abc import Iterable
from enum import Enum
from typing import Any, TypeVar

from app.modules.decision.hard_constraint_fields import (
    DEFAULT_DOMAIN,
    get_default_operators,
    get_field_kind,
    get_request_field_mapping,
    validate_constraint,
)

CandidateT = TypeVar("CandidateT")

# Kiểu cấu hình điều kiện: field_name -> (operator, giá trị)
Constraints = dict[str, tuple[str, Any]]


def _get_field(candidate: Any, field_name: str, default: Any = None) -> Any:
    """Lấy giá trị trường từ dict hoặc object ứng viên."""
    if isinstance(candidate, dict):
        return candidate.get(field_name, default)
    return getattr(candidate, field_name, default)


def _extract_candidate_id(candidate: Any) -> Any | None:
    """Trích xuất ID của ứng viên từ dict hoặc object.

    Trả None khi ứng viên không có ID hợp lệ — không tạo ID giả (0) để tránh
    client hiểu nhầm là ứng viên thực sự có ID bằng 0.
    """
    for field in ("id", "food_id", "destination_id", "item_id"):
        val = _get_field(candidate, field)
        if val is None:
            continue
        if isinstance(val, str) and not val.strip():
            continue
        return val
    return None


def _display_value(value: Any) -> str:
    """Hiển thị giá trị trong message: Enum dùng `.value`, còn lại dùng str()."""
    if isinstance(value, Enum):
        return str(value.value)
    return str(value)


def _extract_candidate_name(candidate: Any) -> str:
    """Trích xuất tên của ứng viên từ dict hoặc object."""
    for field in ("name", "title", "food_name"):
        val = _get_field(candidate, field)
        if val is not None:
            return str(val)
    return "Không tên"


def _normalize_text(value: Any) -> str | None:
    """Chuẩn hóa giá trị text (Enum hoặc str) về chữ thường; None nếu thiếu."""
    if value is None:
        return None
    raw = value.value if isinstance(value, Enum) else str(value)
    normalized = raw.strip().lower()
    return normalized or None


def _to_number(value: Any) -> float | None:
    """Chuyển giá trị thô sang số; trả None nếu thiếu, sai kiểu hoặc không hữu hạn."""
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, ArithmeticError):
        return None
    if math.isnan(number) or number in (float("inf"), float("-inf")):
        return None
    return number


def _as_list(value: Any) -> list[Any] | None:
    """Chuẩn hóa giá trị thành list; None nếu không phải collection (sai định dạng)."""
    if value is None:
        return None
    if isinstance(value, (str, bytes)):
        return None
    if isinstance(value, (list, tuple, set, frozenset)):
        return list(value)
    return None


def _extract_ingredient_names(raw_ingredients: Any) -> list[str] | None:
    """Trích xuất danh sách tên nguyên liệu dạng chữ thường.

    Trả None khi thiếu dữ liệu hoặc sai định dạng (không phải collection) —
    người gọi dùng để loại ứng viên thay vì coi là thoả mãn.
    """
    items = _as_list(raw_ingredients)
    if items is None:
        return None
    names: list[str] = []
    for item in items:
        if isinstance(item, str):
            name = item
        elif isinstance(item, dict):
            name = str(item.get("name", ""))
        else:
            name = str(getattr(item, "name", ""))
        cleaned = name.strip().lower()
        if cleaned:
            names.append(cleaned)
    return names


def _ingredient_matches(ingredient: str, other: str) -> bool:
    """Hai tên nguyên liệu được coi là trùng nhau khi bằng nhau hoặc chứa nhau."""
    return ingredient == other or other in ingredient or ingredient in other


def _compare_number(actual: float, operator: str, expected: Any) -> bool:
    """So sánh số theo operator. `expected` là số cho toán tử đơn, list cho in/not_in."""
    if operator in ("in", "not_in"):
        values = _as_list(expected)
        if values is None:
            raise ValueError(
                f"Operator {operator!r} trên field số cần giá trị là danh sách, nhận {expected!r}."
            )
        numbers = [_to_number(item) for item in values]
        if any(number is None for number in numbers):
            raise ValueError(
                f"Giá trị so sánh cho operator {operator!r} phải là số hợp lệ, nhận {expected!r}."
            )
        contained = actual in [number for number in numbers if number is not None]
        return contained if operator == "in" else not contained

    number = _to_number(expected)
    if number is None:
        raise ValueError(f"Giá trị so sánh không hợp lệ: {expected!r}.")
    if operator == "<=":
        return actual <= number
    if operator == ">=":
        return actual >= number
    if operator == "=":
        return actual == number
    if operator == "!=":
        return actual != number
    raise ValueError(f"Operator không hỗ trợ: {operator!r}.")


def _compare_text(actual: str, operator: str, expected: Any) -> bool:
    """So sánh text (đã chuẩn hóa chữ thường) theo operator."""
    if operator in ("in", "not_in"):
        values = _as_list(expected)
        if values is None:
            raise ValueError(
                f"Operator {operator!r} trên field text cần giá trị là danh sách, "
                f"nhận {expected!r}."
            )
        texts = [text for text in (_normalize_text(item) for item in values) if text]
        contained = any(actual == text for text in texts)
        return contained if operator == "in" else not contained

    text = _normalize_text(expected)
    if text is None:
        raise ValueError(f"Giá trị so sánh không hợp lệ: {expected!r}.")
    if operator == "=":
        return actual == text
    if operator == "!=":
        return actual != text
    raise ValueError(f"Operator {operator!r} không áp dụng được cho field text.")


def _compare_ingredients(actual: list[str], operator: str, expected: Any) -> bool:
    """So sánh danh sách nguyên liệu của ứng viên với danh sách cấu hình.

    - `not_in`: giữ ứng viên khi KHÔNG có nguyên liệu nào trùng với danh sách cần tránh.
    - `in`: giữ ứng viên khi MỌI nguyên liệu đều nằm trong danh sách cho phép.
    """
    values = _as_list(expected)
    if values is None:
        raise ValueError(
            f"Field 'ingredients' cần giá trị là danh sách, nhận {expected!r}."
        )
    texts = [text for text in (_normalize_text(item) for item in values) if text]
    if not texts:
        # Danh sách rỗng không lọc được gì.
        return True

    if operator == "not_in":
        return not any(
            _ingredient_matches(ingredient, text)
            for ingredient in actual
            for text in texts
        )
    if operator == "in":
        return all(
            any(_ingredient_matches(ingredient, text) for text in texts)
            for ingredient in actual
        )
    raise ValueError(
        f"Operator {operator!r} không áp dụng được cho field 'ingredients'."
    )


def _matches_constraint(
    candidate: Any,
    field_name: str,
    operator: str,
    expected: Any,
    domain: str,
) -> bool:
    """Kiểm tra ứng viên có thoả một điều kiện hay không.

    Quy ước dữ liệu thiếu: khi điều kiện đang được áp dụng mà trường dữ liệu
    tương ứng bị thiếu hoặc sai kiểu, ứng viên bị loại (không coi là thoả mãn).
    """
    kind = get_field_kind(domain, field_name)

    if kind == "number":
        number = _to_number(_get_field(candidate, field_name))
        if number is None or number < 0:
            return False
        return _compare_number(number, operator, expected)

    if kind == "text":
        text = _normalize_text(_get_field(candidate, field_name))
        if text is None:
            return False
        return _compare_text(text, operator, expected)

    names = _extract_ingredient_names(_get_field(candidate, field_name))
    if names is None:
        return False
    return _compare_ingredients(names, operator, expected)


def _explain_constraint(
    candidate: Any,
    field_name: str,
    operator: str,
    expected: Any,
) -> str:
    """Sinh chuỗi giải thích lý do cụ thể khi ứng viên vi phạm điều kiện.

    Chỉ xử lý các field của domain Food (price, prep_time, meal_type, ingredients).
    Field ngoài danh sách này trả về thông báo chung ở cuối hàm.
    """
    raw_val = _get_field(candidate, field_name)

    if field_name == "price":
        number = _to_number(raw_val)
        if number is None or number < 0:
            return "Giá không hợp lệ hoặc thiếu thông tin giá."
        if operator == "<=":
            exp_num = _to_number(expected)
            exp_str = f"{int(exp_num):,}đ" if exp_num is not None else str(expected)
            return f"Giá ({int(number):,}đ) vượt quá ngân sách tối đa ({exp_str})."
        if operator == ">=":
            exp_num = _to_number(expected)
            exp_str = f"{int(exp_num):,}đ" if exp_num is not None else str(expected)
            return f"Giá ({int(number):,}đ) thấp hơn mức tối thiểu ({exp_str})."

    elif field_name == "prep_time":
        number = _to_number(raw_val)
        if number is None or number < 0:
            return "Thời gian chuẩn bị không hợp lệ hoặc thiếu dữ liệu."
        if operator == "<=":
            exp_num = _to_number(expected)
            exp_str = f"{int(exp_num)}" if exp_num is not None else str(expected)
            return f"Thời gian chuẩn bị ({int(number)} phút) vượt quá giới hạn tối đa ({exp_str} phút)."

    elif field_name == "meal_type":
        text = _normalize_text(raw_val)
        if text is None:
            return "Thiếu thông tin loại bữa ăn."
        actual_str = _display_value(raw_val)
        if operator == "=":
            return (
                f"Loại bữa ăn '{actual_str}' không phù hợp với bữa ăn yêu cầu "
                f"'{_display_value(expected)}'."
            )
        if operator == "in":
            return f"Loại bữa ăn '{actual_str}' không nằm trong danh sách bữa ăn yêu cầu."

    elif field_name == "ingredients":
        names = _extract_ingredient_names(raw_val)
        if names is None:
            return "Dữ liệu nguyên liệu không hợp lệ hoặc bị thiếu."
        if operator == "not_in":
            values = _as_list(expected) or []
            avoided = [t for t in (_normalize_text(item) for item in values) if t]
            matched = [
                ingredient
                for ingredient in names
                if any(_ingredient_matches(ingredient, t) for t in avoided)
            ]
            if matched:
                return f"Chứa nguyên liệu cần tránh: {', '.join(sorted(set(matched)))}."
            return "Chứa nguyên liệu trong danh sách cần tránh."
        if operator == "in":
            return "Chứa nguyên liệu ngoài danh sách cho phép."

    return f"Không thỏa mãn điều kiện bắt buộc: {field_name} {operator} {expected}."


def inspect_candidate(
    candidate: Any,
    active: Constraints,
    domain: str,
) -> tuple[bool, list[str]]:
    """Kiểm tra ứng viên và trả về (is_valid, danh_sách_lý_do_vi_phạm)."""
    reasons: list[str] = []
    for field_name, (operator, expected) in active.items():
        if not _matches_constraint(candidate, field_name, operator, expected, domain):
            reason = _explain_constraint(candidate, field_name, operator, expected)
            reasons.append(reason)
    return len(reasons) == 0, reasons


def _passes_all(candidate: Any, active: Constraints, domain: str) -> bool:
    """Kiểm tra ứng viên có thoả toàn bộ điều kiện trong `active` hay không."""
    return all(
        _matches_constraint(candidate, field_name, operator, expected, domain)
        for field_name, (operator, expected) in active.items()
    )


def passes_hard_constraints(
    candidate: Any,
    constraints: Constraints | None = None,
    *,
    domain: str = DEFAULT_DOMAIN,
    **legacy: Any,
) -> bool:
    """Kiểm tra ứng viên có thỏa mãn toàn bộ hard constraints hay không.

    Vi phạm ít nhất một điều kiện sẽ trả về False (bị loại).

    Args:
        candidate: Ứng viên (dict hoặc object).
        constraints: Cấu hình điều kiện {field_name: (operator, giá trị)}.
        domain: Domain của cấu hình điều kiện, dùng để tra cấu hình field.
        **legacy: Tham số cũ (budget_max, meal_type, max_prep_time,
            excluded_ingredients) — chuyển đổi về cùng cơ chế `constraints`.

    Raises:
        ValueError: Khi cấu hình điều kiện không hợp lệ.
    """
    return _passes_all(
        candidate, _merge_constraints(constraints, legacy, domain), domain
    )


def filter_and_explain_candidates(
    candidates: Iterable[CandidateT],
    constraints: Constraints | None = None,
    *,
    domain: str = DEFAULT_DOMAIN,
    **legacy: Any,
) -> tuple[list[CandidateT], list[dict[str, Any]]]:
    """Lọc danh sách ứng viên và thống kê chi tiết các phương án bị loại.

    Args:
        candidates: Danh sách ứng viên.
        constraints: Cấu hình điều kiện {field_name: (operator, giá trị)}.
        domain: Domain của cấu hình điều kiện ("food").
        **legacy: Tham số cũ (budget_max, meal_type, max_prep_time, excluded_ingredients).

    Returns:
        tuple (valid_candidates, excluded_candidates):
        - valid_candidates: Danh sách ứng viên thỏa mãn tất cả điều kiện.
        - excluded_candidates: Danh sách thông tin phương án bị loại kèm:
          - id: ID của phương án.
          - name: Tên của phương án.
          - status: "excluded".
          - is_excluded: True.
          - exclusion_reason: Chuỗi lý do cụ thể.
          - exclusion_reasons: Danh sách tất cả lý do vi phạm nếu có nhiều lỗi.
          - candidate: Đối tượng ứng viên gốc.
    """
    active = _merge_constraints(constraints, legacy, domain)
    valid_candidates: list[CandidateT] = []
    excluded_candidates: list[dict[str, Any]] = []

    for candidate in candidates:
        is_valid, reasons = inspect_candidate(candidate, active, domain)
        if is_valid:
            valid_candidates.append(candidate)
        else:
            c_id = _extract_candidate_id(candidate)
            c_name = _extract_candidate_name(candidate)
            reason_str = (
                "; ".join(reasons) if reasons else "Vi phạm điều kiện bắt buộc."
            )
            excluded_candidates.append(
                {
                    "id": c_id,
                    "name": c_name,
                    "status": "excluded",
                    "is_excluded": True,
                    "exclusion_reason": reason_str,
                    "exclusion_reasons": reasons,
                    "candidate": candidate,
                }
            )

    return valid_candidates, excluded_candidates


def filter_candidates(
    candidates: Iterable[CandidateT],
    constraints: Constraints | None = None,
    *,
    domain: str = DEFAULT_DOMAIN,
    **legacy: Any,
) -> list[CandidateT]:
    """Lọc danh sách ứng viên theo hard constraints trước bước chấm điểm.

    Args:
        candidates: Danh sách ứng viên.
        constraints: Cấu hình điều kiện {field_name: (operator, giá trị)}.
        domain: Domain của cấu hình điều kiện, dùng để tra cấu hình field.
        **legacy: Tham số cũ — chuyển đổi về cùng cơ chế `constraints`.

    Raises:
        ValueError: Khi cấu hình điều kiện không hợp lệ.
    """
    active = _merge_constraints(constraints, legacy, domain)
    # Dùng _passes_all() (short-circuit) để dừng ngay tại điều kiện đầu tiên
    # không đạt — ứng viên đã bị loại thì không cần đánh giá các điều kiện sau.
    return [
        candidate
        for candidate in candidates
        if _passes_all(candidate, active, domain)
    ]


def _merge_constraints(
    constraints: Constraints | None,
    legacy: dict[str, Any],
    domain: str,
) -> Constraints:
    """Gộp cấu hình mới và tham số cũ thành một bộ điều kiện duy nhất."""
    active: Constraints = dict(constraints or {})

    if legacy:
        request_mapping = get_request_field_mapping(domain)
        default_operators = get_default_operators(domain)

        for request_field, value in legacy.items():
            if value is None or (isinstance(value, (list, tuple, set)) and not value):
                continue
            field_name = request_mapping.get(request_field)
            if field_name is None:
                raise ValueError(f"Tham số lọc không hợp lệ: {request_field!r}.")
            operator = default_operators[field_name]
            number = _to_number(value)
            if number is not None and number < 0:
                if field_name == "price":
                    raise ValueError("Ngân sách tối đa (budget_max) không được âm.")
                if field_name == "prep_time":
                    raise ValueError(
                        "Thời gian chuẩn bị tối đa (max_prep_time) không được âm."
                    )
            active.setdefault(field_name, (operator, value))

    for field_name, (operator, _expected) in active.items():
        validate_constraint(domain, field_name, operator)

    return active
