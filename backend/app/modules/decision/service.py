"""Service cho module Decision — điều phối nghiệp vụ giữa repository và engine.

Nhận request từ router, gọi repository để lấy dữ liệu,
sau đó gọi Decision Engine để tính điểm và trả kết quả.
Không chứa logic truy vấn DB và không chứa logic tính điểm trực tiếp.
"""

import logging
from enum import Enum
from typing import Any

from fastapi import status
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session

from app.common.exceptions import DecisionHubException, ResourceNotFoundException
from app.modules.decision.criterion_fields import resolve_field_name
from app.modules.decision.decision_response import (
    AppliedFilters,
    CriteriaScores,
    CriterionDetail,
    DecisionResponse,
    ExcludedOptionResponse,
    RecommendedFoodResponse,
    ScoringResponse,
    ScoringWeights,
)
from app.modules.decision.engine.filters import filter_and_explain_candidates
from app.modules.decision.engine.pipeline import MAX_EXCLUDED_DETAIL, evaluate_decision
from app.modules.decision.hard_constraint_fields import (
    get_default_operators,
    get_request_field_mapping,
    validate_constraint,
)
from app.modules.decision.repository import (
    count_decisions_by_user,
    create_decision,
    filter_food_candidates_in_db,
    get_decision_by_id_and_user,
    get_decisions_by_user,
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
from app.modules.decision.schema import (
    DecisionHistoryDetailResponse,
    DecisionHistoryItem,
    DecisionHistoryListResponse,
    DecisionRecommendRequest,
)

from app.modules.travel.adapter import (
        adapt_travel_candidates,
        adapt_travel_criteria,
    )
from app.modules.travel.schemas import TravelExcludedOptionResponse
from app.modules.travel.repository import get_active_travel_places
from app.modules.travel.services import build_travel_decision_response

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


def _food_to_candidate_dict(f: Any) -> dict[str, Any]:
    """Chuyển đổi bản ghi Food ORM hoặc dict sang dict ứng viên chuẩn cho Decision Engine."""
    if isinstance(f, dict):
        return f
    cand_id = getattr(f, "id", 0)
    raw_price = getattr(f, "price", 0.0)
    price_val = float(raw_price) if raw_price is not None else 0.0
    ingredients_list: list[str] = []
    unloaded = (
        sa_inspect(f).unloaded if hasattr(f, "_sa_instance_state") else set()
    )
    f_ingredients = None if "ingredients" in unloaded else getattr(f, "ingredients", None)
    if f_ingredients:
        for ing in f_ingredients:
            if isinstance(ing, str):
                ingredients_list.append(ing)
            elif hasattr(ing, "name"):
                ingredients_list.append(str(ing.name))
    return {
        "id": cand_id,
        "food_id": cand_id,
        "name": getattr(f, "name", ""),
        "price": price_val,
        "prep_time": getattr(f, "prep_time", 0),
        "meal_type": getattr(f, "meal_type", ""),
        "image_url": getattr(f, "image_url", None),
        "tags": _normalize_food_tags(getattr(f, "tags", None)),
        "ingredients": ingredients_list,
    }


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


def recommend_food_decisions(
    db: Session,
    payload: DecisionRecommendRequest,
    user_id: int | None = None,
) -> DecisionResponse:
    """Điều phối toàn bộ quy trình gợi ý món ăn (domain 'food') bằng Decision Engine WSM.

    Quy trình chuẩn:
      Bước 1: Lấy dữ liệu từ Repository (danh sách món ăn, tiêu chí và cấu hình Hard Constraints).
      Bước 2: Xây dựng điều kiện lọc bằng build_food_constraints().
      Bước 3: Gọi Decision Engine pipeline.evaluate_decision() (lọc tiêu chí theo domain,
              phân tách ứng viên hợp lệ/bị loại, chuẩn hóa điểm, tính tổng điểm WSM, xếp hạng).
      Bước 4: Xử lý kết quả, định dạng danh sách món ăn đã xếp hạng và phương án bị loại thành DecisionResponse.

    Args:
        db: SQLAlchemy Session.
        payload: Dữ liệu request từ client (budget_max, meal_type, max_prep_time,
                 excluded_ingredients, preferred_tags, limit).

    Returns:
        DecisionResponse: Chứa danh sách items đã xếp hạng, excluded_items, total, limit, applied_filters, scoring.

    Raises:
        DecisionHubException: Khi cấu hình tiêu chí/ràng buộc sai hoặc gặp lỗi truy vấn.
    """
    # meal_type là Literal[str] nên đã là str; giữ .value cho trường hợp
    # truyền Enum vào (Enum(str) cũng có .value).
    meal_type_val = (
        payload.meal_type.value
        if isinstance(payload.meal_type, Enum)
        else payload.meal_type
    )

    applied_filters = AppliedFilters(
        budget_max=payload.budget_max,
        meal_type=meal_type_val,
        max_prep_time=payload.max_prep_time,
        excluded_ingredients=list(payload.excluded_ingredients or []),
        preferred_tags=list(payload.preferred_tags or []),
    )

    # --------------------------------------------------------------------------
    # BƯỚC 1: Lấy cấu hình tiêu chí và Hard Constraints từ Repository
    # --------------------------------------------------------------------------
    try:
        criteria_objs = get_food_criteria(db)
        hard_constraint_configs = get_food_hard_constraints(db)
        raw_weights = repo_get_food_weights(db)
    except Exception as exc:
        logger.exception("Lỗi khi truy vấn repository trong recommend_food_decisions")
        raise DecisionHubException(
            message=f"Lỗi truy vấn cơ sở dữ liệu: {exc}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from exc

    # Chuẩn hóa cấu hình scoring response
    if payload.weights is not None:
        food_weights = {
            "price": payload.weights.price,
            "preference": payload.weights.preference,
            "prep_time": payload.weights.prep_time,
        }
    else:
        food_weights = _to_engine_weights(raw_weights) if raw_weights else {}

    scoring_weights = ScoringWeights(
        price=food_weights.get("price", 0.40),
        preference=food_weights.get("preference", 0.35),
        prep_time=food_weights.get("prep_time", 0.25),
    )
    scoring_response = ScoringResponse(method="WSM", weights=scoring_weights)

    # Chuẩn hóa criteria cho Engine
    criteria: list[dict[str, Any]] = []
    for c in criteria_objs:
        if isinstance(c, dict):
            crit_dict = dict(c)
        else:
            crit_dict = {
                "domain": getattr(c, "domain", "food"),
                "name": getattr(c, "name", ""),
                "direction": getattr(c, "direction", "min"),
                "weight": float(getattr(c, "weight", 0.0)),
            }
        if payload.weights is not None:
            try:
                fn = resolve_field_name(str(crit_dict.get("name", "")))
                if fn in food_weights:
                    crit_dict["weight"] = food_weights[fn]
            except ValueError:
                pass
        criteria.append(crit_dict)

    if not criteria:
        criteria = [
            {
                "domain": "food",
                "name": "Giá",
                "direction": "min",
                "weight": scoring_weights.price,
            },
            {
                "domain": "food",
                "name": "Mức phù hợp nhu cầu/khẩu vị",
                "direction": "max",
                "weight": scoring_weights.preference,
            },
            {
                "domain": "food",
                "name": "Thời gian chuẩn bị",
                "direction": "min",
                "weight": scoring_weights.prep_time,
            },
        ]

    # --------------------------------------------------------------------------
    # BƯỚC 2: Xây dựng điều kiện lọc (Hard Constraints) & lọc tại Database khi phù hợp
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

    if not constraints:
        # Fallback sang default operators khi DB chưa có cấu hình hard_constraints
        default_ops = get_default_operators("food")
        req_mapping = get_request_field_mapping("food")
        req_vals = {
            "budget_max": payload.budget_max,
            "meal_type": meal_type_val,
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

    try:
        db_filter_result = filter_food_candidates_in_db(db, constraints)
    except Exception as exc:
        logger.exception("Lỗi khi lọc ứng viên tại database trong recommend_food_decisions")
        raise DecisionHubException(
            message=f"Lỗi truy vấn cơ sở dữ liệu: {exc}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from exc

    # --------------------------------------------------------------------------
    # BƯỚC 3: Gọi Decision Engine (pipeline.evaluate_decision)
    # --------------------------------------------------------------------------
    try:
        if db_filter_result is None:
            # Khi DB không trả về món ăn nào (table rỗng hoặc mock DB) → fallback sang dữ liệu mẫu.
            from app.modules.decision.mock_data import RAW_MOCK_CANDIDATES

            logger.info("Không có món ăn trong database, dùng dữ liệu mẫu để demo/test.")
            eval_result = evaluate_decision(
                candidates=list(RAW_MOCK_CANDIDATES),
                criteria=criteria,
                domain="food",
                constraints=constraints,
                user_preferences=payload.preferred_tags,
                limit=payload.limit,
            )
        else:
            (
                sql_matched_foods,
                sql_excluded_sample,
                sql_excluded_count,
                remaining_constraints,
            ) = db_filter_result

            sql_matched_dicts = [_food_to_candidate_dict(f) for f in sql_matched_foods]
            excluded_sample_dicts = [
                _food_to_candidate_dict(f) for f in sql_excluded_sample
            ]

            if not remaining_constraints and sql_matched_dicts:
                # Toàn bộ điều kiện bắt buộc đã được lọc ở database: chỉ chấm điểm tập hợp lệ.
                eval_result = evaluate_decision(
                    candidates=sql_matched_dicts,
                    criteria=criteria,
                    domain="food",
                    constraints=None,
                    user_preferences=payload.preferred_tags,
                    limit=payload.limit,
                )
                if excluded_sample_dicts:
                    _, sql_excluded_details = filter_and_explain_candidates(
                        excluded_sample_dicts,
                        constraints,
                        domain="food",
                    )
                    excluded_detail = sql_excluded_details[:MAX_EXCLUDED_DETAIL]
                    eval_result["excluded_candidates"] = excluded_detail
                    eval_result["excluded_returned_count"] = len(excluded_detail)
                eval_result["total_excluded"] = sql_excluded_count
            else:
                combined_dicts = sorted(
                    sql_matched_dicts + excluded_sample_dicts,
                    key=lambda c: c.get("id") or 0,
                )
                omitted_excluded_count = max(
                    0, sql_excluded_count - len(excluded_sample_dicts)
                )
                eval_result = evaluate_decision(
                    candidates=combined_dicts,
                    criteria=criteria,
                    domain="food",
                    constraints=constraints,
                    user_preferences=payload.preferred_tags,
                    limit=payload.limit,
                )
                eval_result["total_excluded"] = (
                    int(eval_result.get("total_excluded", 0)) + omitted_excluded_count
                )
    except ValueError as val_err:
        logger.error(
            "Lỗi tham số/trọng số khi thực thi Decision Engine evaluate_decision: %s",
            val_err,
        )
        raise DecisionHubException(
            message=f"Lỗi tính toán Decision Engine: {val_err}",
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from val_err
    except Exception as exc:
        logger.exception("Lỗi không mong muốn trong Decision Engine evaluate_decision")
        raise DecisionHubException(
            message=f"Lỗi khi đánh giá và xếp hạng ứng viên: {exc}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from exc

    # --------------------------------------------------------------------------
    # BƯỚC 4: Xử lý kết quả và chuẩn hóa response
    # --------------------------------------------------------------------------
    excluded_items = [
        ExcludedOptionResponse(
            id=exc.get("id")
            if exc.get("id") is not None
            else exc.get("food_id"),
            name=str(exc.get("name") or ""),
            status="excluded",
            is_excluded=True,
            exclusion_reason=str(exc.get("exclusion_reason") or ""),
            exclusion_reasons=exc.get("exclusion_reasons")
            or (
                [str(exc.get("exclusion_reason"))]
                if exc.get("exclusion_reason")
                else []
            ),
        )
        for exc in eval_result.get("excluded_candidates", [])
    ]

    items: list[RecommendedFoodResponse] = []
    pref_lower = [str(t).strip().lower() for t in (payload.preferred_tags or [])]

    for cand in eval_result.get("valid_candidates", []):
        cand_id = int(cand.get("id") or cand.get("food_id") or 0)
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

        details = cand.get("criteria_details") or {}
        crit_details = {
            k: CriterionDetail(
                normalized_score=v.get("normalized_score"),
                weight=float(v.get("weight") or 0.0),
                contribution=float(v.get("contribution") or 0.0),
            )
            for k, v in details.items()
            if isinstance(v, dict)
        }

        reasons = _build_food_reasons(
            price_int=price_int,
            budget_max=payload.budget_max,
            prep_time=prep_time_int,
            max_prep_time=payload.max_prep_time,
            meal_type=cand.get("meal_type"),
            matched_tags=matched_tags,
        )

        score_val = float(cand.get("score") or cand.get("total_score") or 0.0)
        total_score_val = float(cand.get("total_score") or score_val)

        item = RecommendedFoodResponse(
            food_id=cand_id,
            id=cand_id,
            name=str(cand.get("name") or ""),
            price=price_int,
            meal_type=str(cand.get("meal_type") or ""),
            prep_time=prep_time_int,
            image_url=cand.get("image_url"),
            tags=food_tags,
            score=score_val,
            total_score=total_score_val,
            rank=int(cand.get("rank") or 1),
            criteria_scores=criteria_scores,
            criteria_details=crit_details,
            reasons=reasons,
        )
        items.append(item)

    response = DecisionResponse(
        success=bool(eval_result.get("success", True)),
        message=str(eval_result.get("message") or ""),
        has_valid_candidates=bool(
            eval_result.get("has_valid_candidates", len(items) > 0)
        ),
        items=items,
        excluded_items=excluded_items,
        total=len(items),
        total_excluded=int(eval_result.get("total_excluded", len(excluded_items))),
        limit=payload.limit,
        applied_filters=applied_filters,
        scoring=scoring_response,
    )

    # --------------------------------------------------------------------------
    # BƯỚC 5: Lưu lịch sử quyết định khi người dùng đã xác thực
    # --------------------------------------------------------------------------
    if user_id is not None:
        save_decision_history(
            db=db,
            user_id=user_id,
            domain="food",
            input_snapshot=payload.model_dump(mode="json"),
            result_snapshot=response.model_dump(mode="json"),
        )

    return response


def save_decision_history(
    db: Session,
    *,
    user_id: int,
    domain: str,
    input_snapshot: dict[str, Any],
    result_snapshot: dict[str, Any],
) -> DecisionHistoryItem:
    """Lưu bản ghi lịch sử quyết định của người dùng vào bảng `decisions`."""
    try:
        record = create_decision(
            db=db,
            user_id=user_id,
            domain=domain,
            input_snapshot=input_snapshot,
            result_snapshot=result_snapshot,
        )
        return DecisionHistoryItem.model_validate(record)
    except Exception as exc:
        logger.exception("Lỗi khi lưu lịch sử quyết định cho user_id=%s", user_id)
        raise DecisionHubException(
            message="Không thể lưu lịch sử quyết định.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from exc


def list_user_decision_history(
    db: Session,
    *,
    user_id: int,
    limit: int = 20,
    offset: int = 0,
) -> DecisionHistoryListResponse:
    """Lấy danh sách lịch sử quyết định của người dùng đang đăng nhập."""
    records = get_decisions_by_user(
        db=db,
        user_id=user_id,
        limit=limit,
        offset=offset,
    )
    total = count_decisions_by_user(db=db, user_id=user_id)
    items = [DecisionHistoryItem.model_validate(record) for record in records]
    return DecisionHistoryListResponse(
        message="Lấy danh sách lịch sử quyết định thành công.",
        data=items,
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


def get_user_decision_detail(
    db: Session,
    *,
    decision_id: int,
    user_id: int,
) -> DecisionHistoryDetailResponse:
    """Lấy chi tiết một quyết định đã lưu của chính người dùng đang đăng nhập.

    Trả về 404 nếu quyết định không tồn tại hoặc thuộc về người dùng khác.
    """
    if decision_id <= 0:
        raise ResourceNotFoundException("Lịch sử quyết định", decision_id)

    record = get_decision_by_id_and_user(
        db=db,
        decision_id=decision_id,
        user_id=user_id,
    )
    if record is None:
        raise ResourceNotFoundException("Lịch sử quyết định", decision_id)

    item = DecisionHistoryItem.model_validate(record)
    return DecisionHistoryDetailResponse(
        message="Lấy chi tiết lịch sử quyết định thành công.",
        data=item,
        id=item.id,
        user_id=item.user_id,
        domain=item.domain,
        input_snapshot=item.input_snapshot,
        result_snapshot=item.result_snapshot,
        created_at=item.created_at,
    )


def evaluate_travel_recommendation(
    raw_candidates: list[Any],
    payload: Any,
) -> tuple[list[dict[str, Any]], int, list[Any], list[dict[str, Any]]]:
    """Lọc điều kiện cứng và chạy Decision Engine cho danh sách ứng viên Travel."""
    

    adapted_candidates = adapt_travel_candidates(
        raw_candidates,
        preferred_activities=payload.preferred_activities,
    )
    adapted_criteria = adapt_travel_criteria()

    valid_candidates: list[dict[str, Any]] = []
    excluded_items: list[TravelExcludedOptionResponse] = []

    for cand in adapted_candidates:
        reasons: list[str] = []
        cost = int(cand.get("estimated_cost") or 0)
        duration = float(cand.get("estimated_duration") or 0.0)

        if payload.budget_max is not None and cost > payload.budget_max:
            reasons.append(
                f"Chi phí {_format_vnd(cost)} vượt quá ngân sách tối đa {_format_vnd(payload.budget_max)}."
            )
        if payload.max_duration is not None and duration > payload.max_duration:
            reasons.append(
                f"Thời lượng {duration:.1f}h vượt quá thời lượng tối đa {payload.max_duration:.1f}h."
            )
        if payload.region is not None:
            reg_val = payload.region.value
            if cand.get("region") != reg_val:
                reasons.append(
                    f"Khu vực '{cand.get('region')}' không khớp khu vực yêu cầu '{reg_val}'."
                )
        if payload.activity_type is not None and payload.activity_type.strip():
            act_req = payload.activity_type.strip()
            if cand.get("activity_type") != act_req:
                reasons.append(
                    f"Loại hình '{cand.get('activity_type')}' không khớp loại hình yêu cầu '{act_req}'."
                )

        if reasons:
            excluded_items.append(
                TravelExcludedOptionResponse(
                    id=cand.get("id"),
                    name=str(cand.get("name") or ""),
                    status="excluded",
                    is_excluded=True,
                    exclusion_reason="; ".join(reasons),
                    exclusion_reasons=reasons,
                )
            )
        else:
            valid_candidates.append(cand)

    if valid_candidates:
        eval_result = evaluate_decision(
            candidates=valid_candidates,
            criteria=adapted_criteria,
            domain="travel",
            user_preferences=payload.preferred_activities,
            limit=payload.limit,
        )
        ranked_candidates = eval_result.get("valid_candidates", [])
    else:
        ranked_candidates = []

    return ranked_candidates, len(valid_candidates), excluded_items, adapted_criteria


def recommend_travel(
    db: Session,
    payload: Any,
) -> tuple[Any, str]:
    """Lấy dữ liệu từ Travel repository, chấm điểm qua Decision Engine và trả về hiển thị."""
    

    raw_candidates = get_active_travel_places(db)
    ranked_candidates, total_valid, excluded_items, adapted_criteria = (
        evaluate_travel_recommendation(raw_candidates, payload)
    )
    return build_travel_decision_response(
        ranked_candidates=ranked_candidates,
        total_valid=total_valid,
        excluded_items=excluded_items,
        adapted_criteria=adapted_criteria,
        payload=payload,
    )


# Alias tương thích
recommend_food = recommend_food_decisions
recommend_foods = recommend_food_decisions
