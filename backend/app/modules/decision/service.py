"""Service cho module Decision — điều phối nghiệp vụ giữa repository và engine.

Nhận request từ router, gọi repository để lấy dữ liệu,
sau đó gọi Decision Engine để tính điểm và trả kết quả.
Không chứa logic truy vấn DB và không chứa logic tính điểm trực tiếp.
"""

import logging
from typing import Any

from fastapi import status
from sqlalchemy.orm import Session

from app.common.exceptions import DecisionHubException
from app.modules.decision.criterion_fields import resolve_field_name
from app.modules.decision.decision_response import (
    AppliedFilters,
    CriteriaScores,
    DecisionResponse,
    RecommendedFoodResponse,
    ScoringResponse,
    ScoringWeights,
)
from app.modules.decision.engine.pipeline import evaluate
from app.modules.decision.hard_constraint_fields import (
    get_request_field_mapping,
    validate_constraint,
)
from app.modules.decision.repository import (
    get_food_candidates,
    get_food_criteria,
    get_food_hard_constraints,
    get_hard_constraints_by_domain,
)
from app.modules.decision.repository import (
    get_food_weights as repo_get_food_weights,
)
from app.modules.decision.repository import (
    get_travel_weights as repo_get_travel_weights,
)
from app.modules.decision.schema import DecisionRecommendRequest

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
    """Lấy trọng số WSM cho domain food sau khi đã chuẩn hóa sang field_name chuẩn.

    Ủy quyền việc đọc DB cho repository.get_food_weights(db).

    Args:
        db: SQLAlchemy Session.

    Returns:
        dict[str, float]: Trọng số theo `field_name`:
        {"price": ..., "preference": ..., "prep_time": ...}.
    """
    return _to_engine_weights(repo_get_food_weights(db))


def get_travel_weights(db: Session) -> dict[str, float]:
    """Lấy trọng số WSM cho domain travel sau khi đã chuẩn hóa sang field_name chuẩn.

    Ủy quyền việc đọc DB cho repository.get_travel_weights(db).

    Args:
        db: SQLAlchemy Session.

    Returns:
        dict[str, float]: Trọng số travel theo `field_name`
        (vd. "estimated_cost", "estimated_duration", "activities").
    """
    return _to_engine_weights(repo_get_travel_weights(db))


def build_constraints(
    configs_or_db: list[dict[str, str]] | Session,
    domain: str,
    request_values: dict[str, object],
) -> dict[str, tuple[str, object]]:
    """Kết hợp cấu hình HardConstraint với giá trị từ request.

    Hỗ trợ 2 cách dùng:
    - Nhận list `configs` đã lấy từ repository (khuyến nghị, không truy vấn DB trong hàm).
    - Nhận `db` Session (tương thích ngược, ủy quyền đọc DB cho repository).

    Args:
        configs_or_db: Danh sách dict cấu hình hoặc SQLAlchemy Session.
        domain: Domain cần áp dụng cấu hình ("food").
        request_values: Mapping tên field trong request → giá trị
            (vd. {"budget_max": 100000, "meal_type": "lunch"}).

    Returns:
        dict[str, tuple[str, object]]: Mapping field_name → (operator, giá trị).

    Raises:
        ValueError: Khi cấu hình có field_name/operator không hợp lệ.
    """
    if isinstance(configs_or_db, list):
        configs = configs_or_db
    else:
        configs = get_hard_constraints_by_domain(configs_or_db, domain=domain)

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
    configs_or_db: list[dict[str, str]] | Session,
    *,
    budget_max: int | None = None,
    meal_type: str | None = None,
    max_prep_time: int | None = None,
    excluded_ingredients: list[str] | None = None,
) -> dict[str, tuple[str, object]]:
    """Dựng cấu hình lọc ứng viên cho domain food.

    Args:
        configs_or_db: Danh sách cấu hình từ repository hoặc SQLAlchemy Session.
        budget_max: Ngân sách tối đa → field `price`.
        meal_type: Loại bữa ăn → field `meal_type`.
        max_prep_time: Thời gian chuẩn bị tối đa → field `prep_time`.
        excluded_ingredients: Nguyên liệu cần tránh → field `ingredients`.

    Returns:
        dict[str, tuple[str, object]]: Cấu hình cho Decision Engine.
    """
    return build_constraints(
        configs_or_db,
        domain="food",
        request_values={
            "budget_max": budget_max,
            "meal_type": meal_type,
            "max_prep_time": max_prep_time,
            "excluded_ingredients": excluded_ingredients,
        },
    )


def _format_vnd(amount: int) -> str:
    """Format số tiền VND sang định dạng hiển thị (vd: 35000 -> '35.000đ')."""
    return f"{amount:,}".replace(",", ".") + "đ"


def _normalize_food_tags(raw: Any) -> list[str]:
    """Chuẩn hóa tag món ăn từ DB (JSON array hoặc chuỗi phân tách dấu phẩy)."""
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(t).strip() for t in raw if t is not None and str(t).strip()]
    if isinstance(raw, str):
        return [t.strip() for t in raw.split(",") if t.strip()]
    if isinstance(raw, (tuple, set, frozenset)):
        return [str(t).strip() for t in raw if t is not None and str(t).strip()]
    return []


def _build_food_reasons(
    price_int: int,
    budget_max: int,
    prep_time: int,
    max_prep_time: int | None,
    meal_type: str | None,
    matched_tags: list[str],
) -> list[str]:
    """Sinh 1-3 lý do gợi ý dựa trên dữ liệu thực tế và điều kiện đầu vào của người dùng.

    Tuân thủ quy định: chỉ dựa trên dữ liệu thực tế, không suy diễn hoặc bịa đặt.
    """
    reasons: list[str] = []
    if price_int == 0:
        reasons.append("Chi phí 0đ, tối ưu ngân sách")
    else:
        reasons.append(
            f"Giá {_format_vnd(price_int)} nằm trong ngân sách tối đa {_format_vnd(budget_max)}"
        )

    if matched_tags:
        reasons.append(f"Phù hợp khẩu vị ưu tiên: {', '.join(matched_tags)}")
    elif meal_type:
        reasons.append(f"Phù hợp cho bữa {meal_type}")

    if max_prep_time is not None:
        reasons.append(
            f"Thời gian chuẩn bị {prep_time} phút (đạt giới hạn ≤ {max_prep_time} phút)"
        )
    else:
        reasons.append(f"Thời gian chuẩn bị khoảng {prep_time} phút")

    return reasons[:3]


def recommend_food(
    db: Session,
    payload: DecisionRecommendRequest,
) -> DecisionResponse:
    """Điều phối toàn bộ quy trình gợi ý món ăn (domain 'food') bằng Decision Engine WSM.

    Quy trình chuẩn 4 bước:
      Bước 1: Lấy dữ liệu từ Repository (danh sách món ăn, tiêu chí và cấu hình Hard Constraints).
      Bước 2: Xây dựng điều kiện lọc bằng build_food_constraints().
      Bước 3: Gọi Decision Engine pipeline.evaluate() (lọc tiêu chí theo domain,
              lọc ứng viên, chuẩn hóa Min-Max/Preference, tính tổng điểm WSM, xếp hạng).
      Bước 4: Xử lý kết quả, định dạng danh sách món ăn đã xếp hạng thành DecisionResponse.

    Args:
        db: SQLAlchemy Session.
        payload: Dữ liệu request từ client (budget_max, meal_type, max_prep_time,
                 excluded_ingredients, preferred_tags, limit).

    Returns:
        DecisionResponse: Chứa danh sách items đã xếp hạng, total, limit, applied_filters, scoring.

    Raises:
        DecisionHubException: Khi cấu hình tiêu chí/ràng buộc sai hoặc gặp lỗi truy vấn.
    """
    # --------------------------------------------------------------------------
    # BƯỚC 1: Lấy toàn bộ dữ liệu từ Repository (DB queries hoàn toàn nằm ở repo)
    # --------------------------------------------------------------------------
    try:
        candidates = get_food_candidates(db)
        criteria = get_food_criteria(db)
        hard_constraint_configs = get_food_hard_constraints(db)
        raw_weights = repo_get_food_weights(db)
    except Exception as exc:
        logger.exception("Lỗi khi truy vấn repository trong recommend_food")
        raise DecisionHubException(
            message=f"Lỗi truy vấn cơ sở dữ liệu: {exc}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from exc

    if not criteria:
        raise DecisionHubException(
            message="Không tìm thấy cấu hình tiêu chí đánh giá cho domain 'food'.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Chuẩn bị thông tin applied_filters & scoring response
    meal_type_val = (
        payload.meal_type.value
        if hasattr(payload.meal_type, "value")
        else payload.meal_type
    )
    applied_filters = AppliedFilters(
        budget_max=payload.budget_max,
        meal_type=meal_type_val,
        max_prep_time=payload.max_prep_time,
        excluded_ingredients=list(payload.excluded_ingredients or []),
        preferred_tags=list(payload.preferred_tags or []),
    )

    food_weights = _to_engine_weights(raw_weights)
    scoring_weights = ScoringWeights(
        price=food_weights.get("price", 0.40),
        preference=food_weights.get("preference", 0.35),
        prep_time=food_weights.get("prep_time", 0.25),
    )
    scoring_response = ScoringResponse(method="WSM", weights=scoring_weights)

    # Trường hợp DB không có món ăn nào đang hoạt động
    if not candidates:
        logger.info("Không có món ăn nào trong database.")
        return DecisionResponse(
            items=[],
            total=0,
            limit=payload.limit,
            applied_filters=applied_filters,
            scoring=scoring_response,
        )

    # --------------------------------------------------------------------------
    # BƯỚC 2: Xây dựng điều kiện lọc (Hard Constraints)
    # --------------------------------------------------------------------------
    try:
        constraints = build_food_constraints(
            hard_constraint_configs,
            budget_max=payload.budget_max,
            meal_type=meal_type_val,
            max_prep_time=payload.max_prep_time,
            excluded_ingredients=payload.excluded_ingredients,
        )
    except ValueError as val_err:
        logger.error("Cấu hình Hard Constraints không hợp lệ: %s", val_err)
        raise DecisionHubException(
            message=f"Cấu hình điều kiện lọc không hợp lệ: {val_err}",
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from val_err

    # --------------------------------------------------------------------------
    # BƯỚC 3: Gọi Decision Engine (pipeline.evaluate)
    # --------------------------------------------------------------------------
    try:
        ranked_candidates = evaluate(
            candidates=candidates,
            criteria=criteria,
            domain="food",
            constraints=constraints,
            user_preferences=payload.preferred_tags,
        )
    except ValueError as val_err:
        logger.error("Lỗi tham số/trọng số khi thực thi Decision Engine evaluate: %s", val_err)
        raise DecisionHubException(
            message=f"Lỗi tính toán Decision Engine: {val_err}",
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from val_err
    except Exception as exc:
        logger.exception("Lỗi không mong muốn trong Decision Engine evaluate")
        raise DecisionHubException(
            message=f"Lỗi khi đánh giá và xếp hạng ứng viên: {exc}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from exc

    # --------------------------------------------------------------------------
    # BƯỚC 4: Xử lý kết quả và chuẩn hóa response
    # --------------------------------------------------------------------------
    total = len(ranked_candidates)
    top_candidates = ranked_candidates[: payload.limit]

    items: list[RecommendedFoodResponse] = []
    pref_lower = [str(t).strip().lower() for t in (payload.preferred_tags or [])]

    for cand in top_candidates:
        cand_id = int(cand.get("id") or 0)
        raw_price = cand.get("price")
        price_int = round(float(raw_price or 0))
        prep_time_int = int(cand.get("prep_time") or 0)
        food_tags = _normalize_food_tags(cand.get("tags"))
        matched_tags = [t for t in food_tags if t.lower() in pref_lower]

        raw_scores = cand.get("criteria_scores") or {}
        criteria_scores = CriteriaScores(
            price=float(raw_scores.get("price") or 0.0),
            preference=float(raw_scores.get("preference") or 0.0),
            prep_time=float(raw_scores.get("prep_time") or 0.0),
        )

        reasons = _build_food_reasons(
            price_int=price_int,
            budget_max=payload.budget_max,
            prep_time=prep_time_int,
            max_prep_time=payload.max_prep_time,
            meal_type=cand.get("meal_type"),
            matched_tags=matched_tags,
        )

        item = RecommendedFoodResponse(
            food_id=cand_id,
            id=cand_id,
            name=str(cand.get("name") or ""),
            price=price_int,
            meal_type=str(cand.get("meal_type") or ""),
            prep_time=prep_time_int,
            image_url=cand.get("image_url"),
            tags=food_tags,
            score=float(cand.get("score") or 0.0),
            rank=cand.get("rank"),
            criteria_scores=criteria_scores,
            reasons=reasons,
        )
        items.append(item)

    return DecisionResponse(
        items=items,
        total=total,
        limit=payload.limit,
        applied_filters=applied_filters,
        scoring=scoring_response,
    )


# Alias tương thích
recommend_foods = recommend_food

