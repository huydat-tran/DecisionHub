from typing import Any

from app.modules.decision.decision_response import (
    AppliedFilters,
    CriteriaScores,
    CriterionDetail,
    DecisionResponse,
    ExcludedOptionResponse,
    RecommendedFoodResponse,
)
from app.modules.decision.engine.pipeline import evaluate_decision
from app.modules.decision.schema import DecisionRecommendRequest

RAW_MOCK_CANDIDATES: list[dict[str, Any]] = [
    {
        "id": 101,
        "name": "Món A",
        "price": 30000,
        "meal_type": "lunch",
        "prep_time": 15,
        "image_url": None,
        "tags": ["vegetarian", "spicy"],
        "ingredients": ["rau", "đậu phụ"],
    },
    {
        "id": 103,
        "name": "Món C",
        "price": 20000,
        "meal_type": "lunch",
        "prep_time": 20,
        "image_url": None,
        "tags": ["spicy"],
        "ingredients": ["cơm", "ớt"],
    },
    {
        "id": 102,
        "name": "Món B",
        "price": 40000,
        "meal_type": "lunch",
        "prep_time": 10,
        "image_url": None,
        "tags": ["vegetarian"],
        "ingredients": ["nấm", "rau"],
    },
]

DEFAULT_FOOD_CRITERIA: list[dict[str, Any]] = [
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


def build_mock_response(payload: DecisionRecommendRequest) -> DecisionResponse:
    """Tạo response sử dụng Decision Engine trên dữ liệu ứng viên mẫu."""
    eval_result = evaluate_decision(
        candidates=RAW_MOCK_CANDIDATES,
        criteria=DEFAULT_FOOD_CRITERIA,
        domain="food",
        user_preferences=payload.preferred_tags,
        budget_max=payload.budget_max,
        meal_type=payload.meal_type,
        max_prep_time=payload.max_prep_time,
        excluded_ingredients=payload.excluded_ingredients,
        limit=payload.limit,
    )

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
            f"Giá {cand.get('price', 0):,}đ nằm trong ngân sách {payload.budget_max:,}đ",
            f"Thời gian chuẩn bị {cand.get('prep_time', 0)} phút",
        ]
        items.append(
            RecommendedFoodResponse(
                food_id=cand.get("id", 0),
                name=cand.get("name", ""),
                price=cand.get("price", 0),
                meal_type=cand.get("meal_type", ""),
                prep_time=cand.get("prep_time", 0),
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
