"""Service cho module Decision — điều phối nghiệp vụ giữa repository và engine.

Nhận request từ router, gọi repository để lấy dữ liệu,
sau đó gọi Decision Engine để tính điểm và trả kết quả.
Không chứa logic truy vấn DB và không chứa logic tính điểm trực tiếp.
"""

import logging
from typing import Any

from sqlalchemy.orm import Session, selectinload

from app.modules.decision.criterion_fields import resolve_field_name
from app.modules.decision.decision_response import (
    AppliedFilters,
    CriteriaScores,
    CriterionDetail,
    DecisionResponse,
    ExcludedOptionResponse,
    RecommendedFoodResponse,
)
from app.modules.decision.engine.pipeline import evaluate_decision
from app.modules.decision.hard_constraint_fields import (
    get_request_field_mapping,
    validate_constraint,
)
from app.modules.decision.models import DecisionCriterion
from app.modules.decision.repository import (
    get_hard_constraints_by_domain,
    get_weights_by_domain,
)
from app.modules.decision.schema import DecisionRecommendRequest
from app.modules.food.models_food import Food

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
        validate_constraint(
            domain, config["field_name"], config["operator"], config["name"]
        )

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


def recommend_food_decisions(
    db: Session,
    payload: DecisionRecommendRequest,
) -> DecisionResponse:
    """Xử lý đề xuất món ăn theo phương pháp WSM và thống kê phương án bị loại.

    Luồng:
    1. Lấy danh sách món ăn từ database (hoặc dữ liệu mẫu khi DB rỗng).
    2. Lấy tiêu chí và trọng số từ bảng `decision_criteria`.
    3. Dựng cấu hình Hard Constraints từ bảng `hard_constraints` kết hợp giá trị request.
    4. Gọi Decision Engine (evaluate_decision) để lọc, chấm điểm và xếp hạng.
    5. Đóng gói DecisionResponse trả về cho Client.
    """
    # 1. Lấy tiêu chí
    criteria_rows = (
        db.query(DecisionCriterion).filter(DecisionCriterion.domain == "food").all()
    )
    if criteria_rows:
        criteria: list[dict[str, Any]] = [
            {
                "domain": row.domain,
                "name": row.name,
                "direction": row.direction,
                "weight": float(row.weight),
            }
            for row in criteria_rows
        ]
    else:
        criteria = [
            {"domain": "food", "name": "Giá", "direction": "min", "weight": 0.40},
            {
                "domain": "food",
                "name": "Mức phù hợp nhu cầu/khẩu vị",
                "direction": "max",
                "weight": 0.35,
            },
            {
                "domain": "food",
                "name": "Thời gian chuẩn bị",
                "direction": "min",
                "weight": 0.25,
            },
        ]

    # 2. Lấy danh sách ứng viên
    foods = (
        db.query(Food)
        .options(selectinload(Food.ingredients))
        .filter(Food.is_active.is_(True))
        .all()
    )
    if foods:
        candidates: list[dict[str, Any]] = [
            {
                "id": f.id,
                "food_id": f.id,
                "name": f.name,
                "price": float(f.price) if f.price is not None else 0.0,
                "prep_time": f.prep_time,
                "meal_type": f.meal_type,
                "image_url": f.image_url,
                "tags": f.tags or [],
                "ingredients": [ing.name for ing in f.ingredients]
                if f.ingredients
                else [],
            }
            for f in foods
        ]
    else:
        from app.modules.decision.mock_data import RAW_MOCK_CANDIDATES

        candidates = RAW_MOCK_CANDIDATES

    # 3. Dựng điều kiện bắt buộc
    constraints = build_food_constraints(
        db,
        budget_max=payload.budget_max,
        meal_type=payload.meal_type,
        max_prep_time=payload.max_prep_time,
        excluded_ingredients=payload.excluded_ingredients,
    )
    if not constraints:
        # Fallback sang default operators khi DB chưa có cấu hình hard_constraints
        from app.modules.decision.hard_constraint_fields import (
            get_default_operators,
            get_request_field_mapping,
        )

        default_ops = get_default_operators("food")
        req_mapping = get_request_field_mapping("food")
        req_vals = {
            "budget_max": payload.budget_max,
            "meal_type": payload.meal_type,
            "max_prep_time": payload.max_prep_time,
            "excluded_ingredients": payload.excluded_ingredients,
        }
        for rf, val in req_vals.items():
            if val is not None and not (
                isinstance(val, (list, tuple, set)) and not val
            ):
                fn = req_mapping.get(rf)
                if fn and fn in default_ops:
                    constraints[fn] = (default_ops[fn], val)

    # 4. Chạy Decision Engine
    eval_result = evaluate_decision(
        candidates=candidates,
        criteria=criteria,
        domain="food",
        constraints=constraints,
        user_preferences=payload.preferred_tags,
        limit=payload.limit,
    )

    # 5. Đóng gói kết quả
    excluded_items = [
        ExcludedOptionResponse(
            id=exc["id"],
            name=exc["name"],
            status="excluded",
            is_excluded=True,
            exclusion_reason=exc["exclusion_reason"],
            exclusion_reasons=exc.get("exclusion_reasons", [exc["exclusion_reason"]]),
        )
        for exc in eval_result["excluded_candidates"]
    ]

    items: list[RecommendedFoodResponse] = []
    for cand in eval_result["valid_candidates"]:
        scores = cand.get("criteria_scores", {})
        details = cand.get("criteria_details", {})
        crit_details = {
            k: CriterionDetail(
                normalized_score=v.get("normalized_score"),
                weight=v.get("weight", 0.0),
                contribution=v.get("contribution", 0.0),
            )
            for k, v in details.items()
        }
        reasons = [
            f"Giá {int(cand.get('price', 0)):,}đ nằm trong ngân sách {payload.budget_max:,}đ",
            f"Thời gian chuẩn bị {cand.get('prep_time', 0)} phút",
        ]
        items.append(
            RecommendedFoodResponse(
                food_id=cand.get("id", 0),
                name=cand.get("name", ""),
                price=int(cand.get("price", 0)),
                meal_type=cand.get("meal_type", ""),
                prep_time=int(cand.get("prep_time", 0)),
                image_url=cand.get("image_url"),
                tags=cand.get("tags", []),
                score=cand.get("score", 0.0),
                total_score=cand.get("total_score", cand.get("score", 0.0)),
                rank=cand.get("rank", 1),
                criteria_scores=CriteriaScores(
                    price=scores.get("price", 0.0) or 0.0,
                    preference=scores.get("preference", 0.0) or 0.0,
                    prep_time=scores.get("prep_time", 0.0) or 0.0,
                ),
                criteria_details=crit_details,
                reasons=reasons,
            )
        )

    return DecisionResponse(
        success=eval_result["success"],
        message=eval_result["message"],
        has_valid_candidates=eval_result["has_valid_candidates"],
        items=items,
        excluded_items=excluded_items,
        total=len(items),
        total_excluded=eval_result["total_excluded"],
        limit=payload.limit,
        applied_filters=AppliedFilters(
            budget_max=payload.budget_max,
            meal_type=payload.meal_type,
            max_prep_time=payload.max_prep_time,
            excluded_ingredients=payload.excluded_ingredients,
            preferred_tags=payload.preferred_tags,
        ),
    )
