"""Repository cho module Decision — chịu trách nhiệm truy vấn database.

Chỉ chứa logic đọc dữ liệu từ DB, không có business logic.
Service gọi repository để lấy dữ liệu thô rồi chuyển đổi sang định dạng
đầu vào của Decision Engine.
"""

import logging
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.modules.decision.models import Decision, DecisionCriterion, HardConstraint
from app.modules.food.models_food import Food

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


def get_criteria_by_domain(db: Session, domain: str) -> list[DecisionCriterion]:
    """Truy vấn danh sách tiêu chí đánh giá theo domain từ bảng `decision_criteria`.

    Trả về danh sách đối tượng DecisionCriterion đầy đủ (domain, name, direction, weight).
    Nếu DB không có dữ liệu cho domain tương ứng, trả về tiêu chí FALLBACK mặc định.

    Args:
        db: SQLAlchemy Session.
        domain: Tên domain cần lấy tiêu chí ("food" hoặc "travel").

    Returns:
        list[DecisionCriterion]: Danh sách bản ghi tiêu chí.
    """
    rows: list[DecisionCriterion] = (
        db.query(DecisionCriterion)
        .filter(DecisionCriterion.domain == domain)
        .all()
    )

    if not rows:
        logger.warning(
            "Không tìm thấy dữ liệu trong decision_criteria (domain='%s'). "
            "Đang dùng tiêu chí FALLBACK mặc định.",
            domain,
        )
        if domain == "food":
            return [
                DecisionCriterion(
                    domain="food",
                    name="Giá",
                    direction="min",
                    weight=Decimal("0.4000"),
                ),
                DecisionCriterion(
                    domain="food",
                    name="Mức phù hợp nhu cầu/khẩu vị",
                    direction="max",
                    weight=Decimal("0.3500"),
                ),
                DecisionCriterion(
                    domain="food",
                    name="Thời gian chuẩn bị",
                    direction="min",
                    weight=Decimal("0.2500"),
                ),
            ]
        return []

    return rows


def get_food_candidates(db: Session) -> list[Food]:
    """Truy vấn danh sách tất cả món ăn đang hoạt động từ bảng `foods`.

    Sử dụng selectinload để nạp trước danh sách nguyên liệu (ingredients),
    phục vụ cho việc kiểm tra hard constraint loại trừ nguyên liệu mà không gây N+1 query.

    Args:
        db: SQLAlchemy Session.

    Returns:
        list[Food]: Danh sách các món ăn thỏa điều kiện cơ bản (is_active=True, price>=0).
    """
    stmt = (
        select(Food)
        .options(selectinload(Food.ingredients))
        .where(Food.is_active.is_(True), Food.price >= 0)
        .order_by(Food.id.asc())
    )
    return list(db.scalars(stmt).all())


def get_food_criteria(db: Session) -> list[DecisionCriterion]:
    """Truy vấn danh sách tiêu chí đánh giá cho domain food từ DB."""
    return get_criteria_by_domain(db, domain="food")


def get_food_hard_constraints(db: Session) -> list[dict[str, str]]:
    """Truy vấn danh sách cấu hình điều kiện bắt buộc đang active cho domain food từ DB."""
    return get_hard_constraints_by_domain(db, domain="food")


def get_food_weights(db: Session) -> dict[str, float]:
    """Truy vấn trọng số các tiêu chí cho domain food từ DB."""
    return get_weights_by_domain(db, domain="food")


def get_travel_weights(db: Session) -> dict[str, float]:
    """Truy vấn trọng số các tiêu chí cho domain travel từ DB."""
    return get_weights_by_domain(db, domain="travel")


def create_decision(
    db: Session,
    *,
    user_id: int,
    domain: str,
    input_snapshot: dict[str, Any],
    result_snapshot: dict[str, Any],
) -> Decision:
    """Lưu một bản ghi lịch sử quyết định mới vào bảng `decisions`.

    Đảm bảo tính toàn vẹn giao dịch: nếu có lỗi khi ghi DB sẽ rollback ngay.
    """
    decision = Decision(
        user_id=user_id,
        domain=domain,
        input_snapshot=input_snapshot,
        result_snapshot=result_snapshot,
    )
    try:
        db.add(decision)
        db.commit()
        db.refresh(decision)
        return decision
    except Exception:
        db.rollback()
        raise


def get_decisions_by_user(
    db: Session,
    *,
    user_id: int,
    limit: int = 20,
    offset: int = 0,
) -> list[Decision]:
    """Lấy danh sách lịch sử quyết định của người dùng, sắp xếp mới nhất trước."""
    stmt = (
        select(Decision)
        .where(Decision.user_id == user_id)
        .order_by(Decision.created_at.desc(), Decision.id.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def count_decisions_by_user(db: Session, *, user_id: int) -> int:
    """Đếm tổng số bản ghi lịch sử quyết định của người dùng."""
    stmt = select(func.count(Decision.id)).where(Decision.user_id == user_id)
    return int(db.scalar(stmt) or 0)


def get_decision_by_id_and_user(
    db: Session,
    *,
    decision_id: int,
    user_id: int,
) -> Decision | None:
    """Truy vấn chi tiết một quyết định theo `decision_id` và `user_id`."""
    stmt = select(Decision).where(
        Decision.id == decision_id,
        Decision.user_id == user_id,
    )
    return db.scalar(stmt)



