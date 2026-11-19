"""Pipeline quyết định dùng chung: lọc tiêu chí theo domain, lọc ứng viên, chấm điểm, xếp hạng.

Luồng: filters.py → scoring.py → calculator.py → ranking.py
"""

from collections.abc import Sequence
from typing import Any

from app.modules.decision.engine.calculator import calculate_wsm
from app.modules.decision.engine.filters import Constraints, filter_candidates
from app.modules.decision.engine.ranking import rank_candidates
from app.modules.decision.engine.scoring import score_candidates
from app.modules.decision.models import DECISION_DOMAINS


def select_criteria(criteria: list, domain: str) -> list:
    """Giữ lại tiêu chí thuộc đúng domain được yêu cầu."""
    if domain not in DECISION_DOMAINS:
        raise ValueError(f"Domain không hợp lệ: {domain}")
    return [
        criterion
        for criterion in criteria
        if (
            criterion.get("domain") if isinstance(criterion, dict) else getattr(criterion, "domain", None)
        ) == domain
    ]


def evaluate(
    candidates: Sequence[Any],
    criteria: list,
    domain: str,
    constraints: Constraints | None = None,
    user_preferences: Sequence[str] | None = None,
    **legacy: Any,
) -> list[dict]:
    """Chạy pipeline WSM cho một domain.

    Tiêu chí của domain khác bị loại trước khi chuẩn hóa và tính điểm,
    kể cả khi caller truyền chung một danh sách.

    Hard Constraints được truyền từ tầng bên ngoài vào (cấu hình từ DB kết hợp
    giá trị từ request), không truy vấn database bên trong Engine.

    Luồng:
      1. select_criteria()  → lọc tiêu chí theo domain
      2. filter_candidates() → loại ứng viên vi phạm điều kiện bắt buộc
      3. score_candidates()  → chuẩn hóa điểm từng tiêu chí
      4. calculate_wsm()     → kiểm tra weight và tính tổng WSM
      5. rank_candidates()   → sắp xếp giảm dần và tie-break

    Args:
        candidates: Danh sách ứng viên.
        criteria: Danh sách tiêu chí của mọi domain.
        domain: Domain cần chạy ("food" hoặc "travel").
        constraints: Cấu hình điều kiện bắt buộc {field_name: (operator, giá trị)}.
        user_preferences: Sở thích (tag) của người dùng.
            None (mặc định) → tiêu chí `preference` dùng Min-Max trên field
            `preference` sẵn có của ứng viên (hành vi cũ).
            Danh sách → tiêu chí `preference` được chấm bằng cơ chế khớp tag.
        **legacy: Tham số cũ (budget_max, meal_type, max_prep_time,
            excluded_ingredients) — chuyển đổi về cùng cơ chế `constraints`.
    """
    selected = select_criteria(criteria, domain)

    filtered = filter_candidates(candidates, constraints, domain=domain, **legacy)
    if not filtered:
        return []

    scored = score_candidates(filtered, selected, user_preferences=user_preferences)
    calculated = calculate_wsm(scored, selected)
    return rank_candidates(calculated)
