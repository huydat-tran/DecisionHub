"""Repository cho module Decision — chịu trách nhiệm truy vấn database.

Chỉ chứa logic đọc dữ liệu từ DB, không có business logic.
Service gọi repository để lấy dữ liệu thô.
"""

import logging

from sqlalchemy.orm import Session

from app.modules.decision.models import DecisionCriterion

logger = logging.getLogger(__name__)

# Trọng số FALLBACK — dùng khi DB không có dữ liệu cho domain tương ứng
_FALLBACK_WEIGHTS: dict[str, dict[str, float]] = {
    "food": {
        "price": 0.40,
        "preference": 0.35,
        "prep_time": 0.25,
    },
    # "travel": {"cost": 0.40, "rating": 0.35, "distance": 0.25},  # bổ sung khi làm P1
}


def get_weights_by_domain(db: Session, domain: str) -> dict[str, float]:
    """Truy vấn trọng số WSM theo domain từ bảng `decision_criteria`.

    Query tất cả hàng có domain khớp, build dict: tên tiêu chí → trọng số.

    Ví dụ trả về cho domain='food':
        {"price": 0.40, "preference": 0.35, "prep_time": 0.25}

    Nếu DB không có dữ liệu → dùng _FALLBACK_WEIGHTS[domain] và ghi log cảnh báo.

    Args:
        db: SQLAlchemy Session.
        domain: Tên domain cần lấy trọng số ("food" hoặc "travel").

    Returns:
        dict[str, float]: Mapping tên tiêu chí → trọng số (float).
    """
    rows: list[DecisionCriterion] = (
        db.query(DecisionCriterion)
        .filter(DecisionCriterion.domain == domain)
        .all()
    )

    if not rows:
        logger.warning(
            "Không tìm thấy dữ liệu trong decision_criteria (domain='%s'). "
            "Đang dùng trọng số FALLBACK mặc định.",
            domain,
        )
        return dict(_FALLBACK_WEIGHTS.get(domain, {}))

    # Build dict từ kết quả DB (Decimal → float)
    return {row.name: float(row.weight) for row in rows}
