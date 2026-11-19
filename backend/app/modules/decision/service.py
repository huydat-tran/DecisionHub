"""Service cho module Decision — điều phối nghiệp vụ giữa repository và engine.

Nhận request từ router, gọi repository để lấy dữ liệu,
sau đó gọi Decision Engine để tính điểm và trả kết quả.
Không chứa logic truy vấn DB và không chứa logic tính điểm trực tiếp.
"""

import logging

from sqlalchemy.orm import Session

from app.modules.decision.criterion_fields import resolve_field_name
from app.modules.decision.hard_constraint_fields import (
    get_request_field_mapping,
    validate_constraint,
)
from app.modules.decision.repository import get_hard_constraints_by_domain, get_weights_by_domain

logger = logging.getLogger(__name__)


def _to_engine_weights(raw_weights: dict[str, float]) -> dict[str, float]:
    """Chuyển trọng số từ tên tiêu chí trong DB sang `field_name` chuẩn.

    Decision Engine dùng `field_name` làm key tính toán (khớp với key của
    `criteria_scores`), nên tên hiển thị trong DB (vd. "Giá") không được dùng
    làm key. Việc ánh xạ nằm ở Service để Repository giữ đúng vai trò đọc DB.

    Args:
        raw_weights: Mapping tên tiêu chí → trọng số, lấy từ repository.

    Returns:
        Mapping `field_name` → trọng số.

    Raises:
        ValueError: Khi có tên tiêu chí không ánh xạ được về field_name.
    """
    return {resolve_field_name(name): weight for name, weight in raw_weights.items()}


def get_food_weights(db: Session) -> dict[str, float]:
    """Lấy trọng số WSM cho domain food từ DB.

    Service biết khi nào cần gọi repository và với tham số nào.
    Router không cần biết domain là gì, chỉ gọi service.

    Args:
        db: SQLAlchemy Session (inject từ Depends(get_db) ở router).

    Returns:
        dict[str, float]: Trọng số theo `field_name`:
        {"price": ..., "preference": ..., "prep_time": ...}.
    """
    return _to_engine_weights(get_weights_by_domain(db, domain="food"))


def get_travel_weights(db: Session) -> dict[str, float]:
    """Lấy trọng số WSM cho domain travel từ DB.

    Bổ sung khi triển khai Travel (P1).

    Args:
        db: SQLAlchemy Session.

    Returns:
        dict[str, float]: Trọng số travel theo `field_name`
        (vd. "estimated_cost", "estimated_duration", "activities").
    """
    return _to_engine_weights(get_weights_by_domain(db, domain="travel"))


def build_constraints(
    db: Session,
    domain: str,
    request_values: dict[str, object],
) -> dict[str, tuple[str, object]]:
    """Kết hợp cấu hình HardConstraint từ DB với giá trị từ request.

    Cấu hình DB quy định điều kiện nào được áp dụng và dùng toán tử nào;
    request chỉ cung cấp giá trị thực tế. Kết quả là dict cấu hình mà
    Decision Engine nhận trực tiếp:
    {"price": ("<=", 100000), "meal_type": ("=", "lunch"), ...}

    Args:
        db: SQLAlchemy Session.
        domain: Domain cần lấy cấu hình ("food").
        request_values: Mapping tên field trong request → giá trị
            (vd. {"budget_max": 100000, "meal_type": "lunch"}).

    Returns:
        dict[str, tuple[str, object]]: Mapping field_name → (operator, giá trị).

    Raises:
        ValueError: Khi cấu hình trong DB có field_name/operator không hợp lệ.
    """
    configs = get_hard_constraints_by_domain(db, domain=domain)

    # Kiểm tra toàn bộ cấu hình active trước: cấu hình sai phải báo lỗi rõ ràng,
    # không được âm thầm bỏ qua (sẽ lọt ứng viên vi phạm điều kiện bắt buộc).
    for config in configs:
        validate_constraint(domain, config["field_name"], config["operator"], config["name"])

    by_field = {config["field_name"]: config for config in configs}
    request_mapping = get_request_field_mapping(domain)

    constraints: dict[str, tuple[str, object]] = {}
    for request_field, value in request_values.items():
        field_name = request_mapping.get(request_field)
        if field_name is None:
            logger.warning(
                "Request field %r không có ánh xạ sang field của HardConstraint — bỏ qua.",
                request_field,
            )
            continue

        if value is None or (isinstance(value, (list, tuple, set)) and not value):
            # Không có giá trị → không áp dụng điều kiện.
            continue

        config = by_field.get(field_name)
        if config is None:
            logger.warning(
                "Request có giá trị cho %r nhưng database không có hard constraint "
                "active tương ứng (field_name=%r, domain=%r) — điều kiện không được áp dụng.",
                request_field,
                field_name,
                domain,
            )
            continue

        constraints[field_name] = (config["operator"], value)

    return constraints


def build_food_constraints(
    db: Session,
    *,
    budget_max: int | None = None,
    meal_type: str | None = None,
    max_prep_time: int | None = None,
    excluded_ingredients: list[str] | None = None,
) -> dict[str, tuple[str, object]]:
    """Dựng cấu hình lọc ứng viên cho domain food.

    Args:
        db: SQLAlchemy Session.
        budget_max: Ngân sách tối đa → field `price`.
        meal_type: Loại bữa ăn → field `meal_type`.
        max_prep_time: Thời gian chuẩn bị tối đa → field `prep_time`.
        excluded_ingredients: Nguyên liệu cần tránh → field `ingredients`.

    Returns:
        dict[str, tuple[str, object]]: Cấu hình cho Decision Engine.
    """
    return build_constraints(
        db,
        domain="food",
        request_values={
            "budget_max": budget_max,
            "meal_type": meal_type,
            "max_prep_time": max_prep_time,
            "excluded_ingredients": excluded_ingredients,
        },
    )
