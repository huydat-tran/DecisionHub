"""Bộ lọc điều kiện bắt buộc (Hard Constraints) cho Decision Engine.

Module này chạy thuần Python trên danh sách ứng viên đã chuẩn hóa,
không truy vấn database. Vi phạm bất kỳ điều kiện bắt buộc nào
ứng viên sẽ bị loại ngay trước khi chấm điểm WSM.
"""

from collections.abc import Iterable, Sequence
from decimal import Decimal
from enum import Enum
import math
from typing import Any, TypeVar

CandidateT = TypeVar("CandidateT")


def _to_finite_float(raw: Any) -> float | None:
    """Chuyển giá trị số sang float hữu hạn; trả về None nếu thiếu hoặc không hợp lệ."""
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


def _normalize_meal_type(value: Any) -> str | None:
    """Chuẩn hóa loại bữa ăn (Enum hoặc str) về chữ thường."""
    if value is None:
        return None
    raw = value.value if isinstance(value, Enum) else str(value)
    normalized = raw.strip().lower()
    return normalized or None


def _extract_ingredient_names(raw_ingredients: Any) -> list[str]:
    """Trích xuất danh sách tên nguyên liệu dạng chữ thường."""
    if not raw_ingredients:
        return []
    items = [raw_ingredients] if isinstance(raw_ingredients, str) else raw_ingredients
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


def passes_hard_constraints(
    candidate: Any,
    *,
    budget_max: int | float | Decimal | None = None,
    meal_type: str | Enum | None = None,
    excluded_ingredients: Sequence[str] | None = None,
) -> bool:
    """Kiểm tra ứng viên có thỏa mãn toàn bộ hard constraints hay không.

    Vi phạm ít nhất một điều kiện sẽ trả về False (bị loại).
    """
    if budget_max is not None:
        max_budget = _to_finite_float(budget_max)
        if max_budget is None or max_budget < 0:
            raise ValueError("Ngân sách tối đa (budget_max) không được âm hoặc không hợp lệ.")
        price = _to_finite_float(_get_field(candidate, "price"))
        if price is None or price < 0 or price > max_budget:
            return False

    required_meal = _normalize_meal_type(meal_type)
    if required_meal is not None:
        candidate_meal = _normalize_meal_type(_get_field(candidate, "meal_type"))
        if candidate_meal != required_meal:
            return False

    if excluded_ingredients:
        excluded_lower = [
            item.strip().lower() for item in excluded_ingredients if item and item.strip()
        ]
        if excluded_lower:
            ing_names = _extract_ingredient_names(_get_field(candidate, "ingredients"))
            if any(excl in ing_name for excl in excluded_lower for ing_name in ing_names):
                return False

    return True


def filter_candidates(
    candidates: Iterable[CandidateT],
    *,
    budget_max: int | float | Decimal | None = None,
    meal_type: str | Enum | None = None,
    excluded_ingredients: Sequence[str] | None = None,
) -> list[CandidateT]:
    """Lọc danh sách ứng viên theo hard constraints trước bước chấm điểm."""
    if budget_max is not None:
        max_budget = _to_finite_float(budget_max)
        if max_budget is None or max_budget < 0:
            raise ValueError("Ngân sách tối đa (budget_max) không được âm hoặc không hợp lệ.")

    return [
        candidate
        for candidate in candidates
        if passes_hard_constraints(
            candidate,
            budget_max=budget_max,
            meal_type=meal_type,
            excluded_ingredients=excluded_ingredients,
        )
    ]
