"""Bộ lọc điều kiện bắt buộc (Hard Constraints) cho Decision Engine.

Module này chạy thuần Python trên danh sách ứng viên đã chuẩn hóa,
không truy vấn database. Vi phạm bất kỳ điều kiện bắt buộc nào
ứng viên sẽ bị loại ngay trước khi chấm điểm WSM.
"""

from collections.abc import Iterable, Sequence
from decimal import Decimal
from enum import Enum
from typing import Any, TypeVar

CandidateT = TypeVar("CandidateT")


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
    names: list[str] = []
    for item in raw_ingredients:
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
        raw_price = _get_field(candidate, "price")
        if raw_price is None:
            return False
        price = float(raw_price)
        if price < 0 or price > float(budget_max):
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
    if budget_max is not None and float(budget_max) < 0:
        raise ValueError("Ngân sách tối đa (budget_max) không được âm.")

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
