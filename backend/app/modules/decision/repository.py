"""Truy vấn tiêu chí quyết định theo domain."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.decision.models import DECISION_DOMAINS, DecisionCriterion


def list_criteria_by_domain(db: Session, domain: str) -> list[DecisionCriterion]:
    """Lấy tiêu chí của đúng một domain, sắp theo id.

    Food và Travel không được trộn trong cùng một lần truy vấn phục vụ chấm điểm.
    """
    if domain not in DECISION_DOMAINS:
        raise ValueError(f"Domain không hợp lệ: {domain}")
    stmt = (
        select(DecisionCriterion)
        .where(DecisionCriterion.domain == domain)
        .order_by(DecisionCriterion.id)
    )
    return list(db.scalars(stmt).all())
