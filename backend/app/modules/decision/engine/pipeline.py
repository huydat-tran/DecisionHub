"""Pipeline quyết định dùng chung: lọc tiêu chí theo domain, chấm điểm, xếp hạng.

Luồng: scoring.py → calculator.py → ranking.py
"""

from app.modules.decision.engine.calculator import calculate_wsm
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


def evaluate(candidates: list[dict], criteria: list, domain: str) -> list[dict]:
    """Chạy pipeline WSM cho một domain.

    Tiêu chí của domain khác bị loại trước khi chuẩn hóa và tính điểm,
    kể cả khi caller truyền chung một danh sách.

    Luồng:
      1. score_candidates()  → chuẩn hóa điểm từng tiêu chí
      2. calculate_wsm()     → kiểm tra weight và tính tổng WSM
      3. rank_candidates()   → sắp xếp giảm dần và tie-break
    """
    selected = select_criteria(criteria, domain)
    scored = score_candidates(candidates, selected)
    calculated = calculate_wsm(scored, selected)
    return rank_candidates(calculated)
