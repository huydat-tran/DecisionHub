"""Repository cho module Decision — chịu trách nhiệm truy vấn database.

Chỉ chứa logic đọc dữ liệu từ DB, không có business logic.
Service gọi repository để lấy dữ liệu thô rồi chuyển đổi sang định dạng
đầu vào của Decision Engine.
"""

import logging

from sqlalchemy.orm import Session

from app.modules.decision.models import DecisionCriterion, HardConstraint

logger = logging.getLogger(__name__)

# Trọng số FALLBACK — dùng khi DB không có dữ liệu cho domain tương ứng.
# Key dùng field_name chuẩn (giống key Service trả về sau khi chuyển đổi).
_FALLBACK_WEIGHTS: dict[str, dict[str, float]] = {
    "food": {
        "price": 0.40,
        "preference": 0.35,
        "prep_time": 0.25,
    },
    # "travel": {"estimated_cost": 0.40, "estimated_duration": 0.30, "activities": 0.30},
}


def get_weights_by_domain(db: Session, domain: str) -> dict[str, float]:
    """Truy vấn trọng số WSM theo domain từ bảng `decision_criteria`.

    Query tất cả hàng có domain khớp, build dict: tên tiêu chí → trọng số.

    Key trả về là tên tiêu chí lưu trong DB (vd. "Giá"); Service chịu trách
    nhiệm ánh xạ sang `field_name` chuẩn (vd. "price") trước khi đưa vào
    Decision Engine.

    Ví dụ trả về cho domain='food':
        {"Giá": 0.40, "Mức phù hợp nhu cầu/khẩu vị": 0.35, "Thời gian chuẩn bị": 0.25}

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


def get_hard_constraints_by_domain(db: Session, domain: str) -> list[dict[str, str]]:
    """Truy vấn cấu hình điều kiện bắt buộc theo domain từ bảng `hard_constraints`.

    Chỉ trả về các bản ghi `is_active = True`. Repository không kiểm tra
    `field_name`/`operator` có hợp lệ hay không — việc đó thuộc Service.

    Args:
        db: SQLAlchemy Session.
        domain: Tên domain cần lấy cấu hình ("food" hoặc "travel").

    Returns:
        list[dict[str, str]]: Danh sách {"name", "field_name", "operator"}.
    """
    rows: list[HardConstraint] = (
        db.query(HardConstraint)
        .filter(HardConstraint.domain == domain, HardConstraint.is_active.is_(True))
        .order_by(HardConstraint.id)
        .all()
    )

    if not rows:
        logger.warning(
            "Không tìm thấy hard_constraints đang active (domain='%s'). "
            "Ứng viên sẽ không bị áp dụng điều kiện lọc nào.",
            domain,
        )

    return [
        {"name": row.name, "field_name": row.field_name, "operator": row.operator}
        for row in rows
    ]
