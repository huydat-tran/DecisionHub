"""Nghiệp vụ tìm kiếm, xem chi tiết và gợi ý món ăn (module Food)."""

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from app.common.exceptions import ResourceNotFoundException
from app.modules.decision.decision_response import (
    AppliedFilters,
    CriteriaScores,
    DecisionResponse,
    RecommendedFoodResponse,
    ScoringResponse,
    ScoringWeights,
)
from app.modules.food.models_food import Food
from app.modules.food.schemas_food import (
    FoodOut,
    FoodQuickSearchData,
    FoodQuickSearchFilters,
    FoodRecommendRequest,
    FoodSortBy,
    MealType,
    normalize_tags,
)

# Trọng số mặc định theo rubric Food trong DecisionHub.md (tổng = 1.0)
WEIGHT_PRICE = 0.40
WEIGHT_PREFERENCE = 0.35
WEIGHT_PREP_TIME = 0.25

MEAL_TYPE_LABELS = {
    MealType.BREAKFAST.value: "sáng",
    MealType.LUNCH.value: "trưa",
    MealType.DINNER.value: "tối",
    MealType.SNACK.value: "nhẹ",
}


def _build_food_stmt(
    meal_type: MealType | None,
    max_price: int | None,
    max_prep_time: int | None,
    *,
    require_prep_time: bool = False,
) -> Select[tuple[Food]]:
    """Tạo truy vấn lấy các món ăn đang hoạt động thỏa điều kiện SQL cơ bản."""
    stmt = (
        select(Food)
        .options(selectinload(Food.ingredients))
        .where(Food.is_active.is_(True), Food.price >= 0)
    )
    if meal_type is not None:
        stmt = stmt.where(func.lower(Food.meal_type) == meal_type.value)
    if max_price is not None:
        stmt = stmt.where(Food.price <= max_price)
    if require_prep_time:
        stmt = stmt.where(Food.prep_time.is_not(None), Food.prep_time >= 0)
    if max_prep_time is not None:
        stmt = stmt.where(Food.prep_time.is_not(None), Food.prep_time <= max_prep_time)
    return stmt


def _has_excluded_ingredient(food: Food, excluded_lower: list[str]) -> bool:
    if not excluded_lower:
        return False
    ing_names = [ing.name.lower() for ing in food.ingredients]
    return any(excl in ing_name for excl in excluded_lower for ing_name in ing_names)


def _clamp_score(value: float) -> float:
    return max(0.0, min(100.0, value))


def _format_vnd(amount: int) -> str:
    return f"{amount:,}".replace(",", ".") + "đ"


def _keyword_relevance(food: Food, keyword: str, food_tags: list[str]) -> int:
    """Tính độ liên quan đơn giản theo từ khóa trên tên, nguyên liệu, nhãn và mô tả."""
    kw = keyword.lower()
    name_lower = food.name.lower()
    score = 0

    if name_lower == kw:
        score += 100
    elif name_lower.startswith(kw):
        score += 80
    elif kw in name_lower:
        score += 60

    if any(kw in ing.name.lower() for ing in food.ingredients):
        score += 40
    if any(kw in tag.lower() for tag in food_tags) or kw in food.meal_type.lower():
        score += 30
    if food.description and kw in food.description.lower():
        score += 20

    return score


def quick_search_foods(
    db: Session,
    filters: FoodQuickSearchFilters,
    limit: int,
    offset: int,
) -> tuple[FoodQuickSearchData, str]:
    """Tìm kiếm nhanh món ăn theo từ khóa, bộ lọc và sắp xếp."""
    stmt = _build_food_stmt(
        meal_type=filters.meal_type,
        max_price=filters.max_price,
        max_prep_time=filters.max_prep_time,
    )
    candidates = list(db.scalars(stmt).all())

    # shortcut: lọc excluded_ingredients, tags và tính relevance trên tập đã lọc SQL;
    # chuyển sang SQL JSON/full-text khi catalog vượt vài nghìn món.
    excluded_lower = [item.lower() for item in filters.excluded_ingredients]
    required_tags = [item.lower() for item in filters.tags]
    matched: list[tuple[Food, int]] = []

    for food in candidates:
        if _has_excluded_ingredient(food, excluded_lower):
            continue

        food_tags = normalize_tags(food.tags)
        if required_tags:
            food_tag_set = {t.lower() for t in food_tags}
            if not all(tag in food_tag_set for tag in required_tags):
                continue

        relevance = 0
        if filters.q is not None:
            relevance = _keyword_relevance(food, filters.q, food_tags)
            if relevance == 0:
                continue

        matched.append((food, relevance))

    if filters.sort_by == FoodSortBy.PRICE_ASC:
        matched.sort(
            key=lambda item: (
                int(round(item[0].price)),
                item[0].prep_time is None,
                item[0].prep_time or 0,
                item[0].name.lower(),
                item[0].id,
            )
        )
    elif filters.sort_by == FoodSortBy.PREP_TIME_ASC:
        matched.sort(
            key=lambda item: (
                item[0].prep_time is None,
                item[0].prep_time or 0,
                int(round(item[0].price)),
                item[0].name.lower(),
                item[0].id,
            )
        )
    else:
        matched.sort(key=lambda item: (-item[1], item[0].name.lower(), item[0].id))

    total = len(matched)
    paged_items = [FoodOut.model_validate(food) for food, _ in matched[offset : offset + limit]]

    data = FoodQuickSearchData(
        items=paged_items,
        total=total,
        limit=limit,
        offset=offset,
        filters_applied=filters,
    )
    if total == 0:
        message = "Không tìm thấy món ăn phù hợp. Hãy thử đổi từ khóa hoặc nới lỏng bộ lọc."
    else:
        message = f"Tìm thấy {total} món ăn phù hợp."
    return data, message


def get_food_detail(db: Session, food_id: int) -> FoodOut:
    """Lấy thông tin chi tiết của một món ăn đang hoạt động theo ID."""
    stmt = (
        select(Food)
        .options(selectinload(Food.ingredients))
        .where(Food.id == food_id, Food.is_active.is_(True))
    )
    food = db.scalar(stmt)
    if food is None:
        raise ResourceNotFoundException("Món ăn", food_id)
    return FoodOut.model_validate(food)


def _build_reasons(
    price_int: int,
    budget_max: int,
    prep_time: int,
    max_prep_time: int | None,
    meal_type: MealType | None,
    matched_tags: list[str],
) -> list[str]:
    """Sinh 1-3 lý do dựa trên dữ liệu thực tế và điều kiện đầu vào."""
    reasons: list[str] = []
    if price_int == 0:
        reasons.append("Chi phí 0đ, tối ưu ngân sách")
    else:
        reasons.append(
            f"Giá {_format_vnd(price_int)} nằm trong ngân sách tối đa {_format_vnd(budget_max)}"
        )

    if matched_tags:
        reasons.append(f"Phù hợp khẩu vị ưu tiên: {', '.join(matched_tags)}")
    elif meal_type is not None:
        reasons.append(f"Phù hợp cho bữa {MEAL_TYPE_LABELS[meal_type.value]}")

    if max_prep_time is not None:
        reasons.append(
            f"Thời gian chuẩn bị {prep_time} phút (đạt giới hạn ≤ {max_prep_time} phút)"
        )
    else:
        reasons.append(f"Thời gian chuẩn bị khoảng {prep_time} phút")

    return reasons[:3]


def recommend_foods(
    db: Session,
    payload: FoodRecommendRequest,
) -> tuple[DecisionResponse, str]:
    """Lọc điều kiện bắt buộc, chấm điểm WSM và xếp hạng gợi ý món ăn."""
    # shortcut: tạm đặt WSM scoring/ranking trong food/services.py do decision/engine đang trống;
    # tách sang app/modules/decision/engine khi module decision hoàn thiện.
    stmt = _build_food_stmt(
        meal_type=payload.meal_type,
        max_price=payload.budget_max,
        max_prep_time=payload.max_prep_time,
        require_prep_time=True,
    )
    candidates = list(db.scalars(stmt).all())

    excluded_lower = [item.lower() for item in payload.excluded_ingredients]
    pref_lower = [item.lower() for item in payload.preferred_tags]

    scored: list[tuple[float, int, int, str, int, RecommendedFoodResponse]] = []

    for food in candidates:
        if _has_excluded_ingredient(food, excluded_lower):
            continue

        # require_prep_time=True ở trên đã loại prep_time is None; kiểm tra lại để an toàn kiểu.
        if food.prep_time is None:
            continue

        price_int = int(round(food.price))
        prep_time = food.prep_time
        food_tags = normalize_tags(food.tags)

        if payload.budget_max == 0:
            price_score = 100.0 if price_int == 0 else 0.0
        else:
            price_score = _clamp_score(100.0 * (1.0 - price_int / payload.budget_max))

        if not pref_lower:
            matched_tags: list[str] = []
            preference_score = 50.0
        else:
            food_tag_map = {tag.lower(): tag for tag in food_tags}
            matched_tags = [food_tag_map[tag] for tag in pref_lower if tag in food_tag_map]
            preference_score = _clamp_score(100.0 * len(matched_tags) / len(pref_lower))

        if payload.max_prep_time is None:
            prep_time_score = 50.0
        elif payload.max_prep_time == 0:
            prep_time_score = 100.0 if prep_time == 0 else 0.0
        else:
            prep_time_score = _clamp_score(100.0 * (1.0 - prep_time / payload.max_prep_time))

        total_score = _clamp_score(
            WEIGHT_PRICE * price_score
            + WEIGHT_PREFERENCE * preference_score
            + WEIGHT_PREP_TIME * prep_time_score
        )

        item = RecommendedFoodResponse(
            food_id=food.id,
            name=food.name,
            price=price_int,
            meal_type=food.meal_type,
            prep_time=prep_time,
            image_url=food.image_url,
            tags=food_tags,
            score=round(total_score, 2),
            criteria_scores=CriteriaScores(
                price=round(price_score, 2),
                preference=round(preference_score, 2),
                prep_time=round(prep_time_score, 2),
            ),
            reasons=_build_reasons(
                price_int=price_int,
                budget_max=payload.budget_max,
                prep_time=prep_time,
                max_prep_time=payload.max_prep_time,
                meal_type=payload.meal_type,
                matched_tags=matched_tags,
            ),
        )
        scored.append((total_score, price_int, prep_time, food.name.lower(), food.id, item))

    # Xếp hạng: điểm giảm dần; hòa điểm ưu tiên giá thấp hơn, thời gian ngắn hơn, rồi tên/ID.
    scored.sort(key=lambda row: (-row[0], row[1], row[2], row[3], row[4]))
    top_items = [row[5] for row in scored[: payload.limit]]

    decision_data = DecisionResponse(
        items=top_items,
        total=len(scored),
        limit=payload.limit,
        applied_filters=AppliedFilters(
            budget_max=payload.budget_max,
            meal_type=payload.meal_type.value if payload.meal_type is not None else None,
            max_prep_time=payload.max_prep_time,
            excluded_ingredients=payload.excluded_ingredients,
            preferred_tags=payload.preferred_tags,
        ),
        scoring=ScoringResponse(
            method="WSM",
            weights=ScoringWeights(
                price=WEIGHT_PRICE,
                preference=WEIGHT_PREFERENCE,
                prep_time=WEIGHT_PREP_TIME,
            ),
        ),
    )

    if not top_items:
        message = (
            "Không có món ăn nào thỏa mãn toàn bộ điều kiện. "
            "Hãy thử tăng ngân sách tối đa, nới thời gian chuẩn bị hoặc giảm nguyên liệu cần tránh."
        )
    else:
        message = f"Đề xuất {len(top_items)} món ăn phù hợp nhất."

    return decision_data, message
