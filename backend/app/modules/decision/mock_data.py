from app.modules.decision.schema import DecisionRecommendRequest

from app.modules.decision.decision_response import (
    AppliedFilters,
    CriteriaScores,
    DecisionResponse,
    RecommendedFoodResponse,
    ScoringResponse,
    ScoringWeights,
)

# Đã xếp hạng sẵn: A (63.50) -> C (49.83) -> B (42.17)
MOCK_ITEMS: list[RecommendedFoodResponse] = [
    RecommendedFoodResponse(
        food_id=101,
        name="Món A",
        price=30000,
        meal_type="lunch",
        prep_time=15,
        image_url=None,
        tags=["vegetarian", "spicy"],
        score=63.50,
        criteria_scores=CriteriaScores(price=40.00, preference=100.00, prep_time=50.00),
        reasons=[
            "Phù hợp với 2/2 sở thích đã chọn",
            "Giá 30.000đ nằm trong ngân sách 50.000đ",
        ],
    ),
    RecommendedFoodResponse(
        food_id=103,
        name="Món C",
        price=20000,
        meal_type="lunch",
        prep_time=20,
        image_url=None,
        tags=["spicy"],
        score=49.83,
        criteria_scores=CriteriaScores(price=60.00, preference=50.00, prep_time=33.33),
        reasons=[
            "Phù hợp với 1/2 sở thích đã chọn",
            "Giá 20.000đ nằm trong ngân sách 50.000đ",
        ],
    ),
    RecommendedFoodResponse(
        food_id=102,
        name="Món B",
        price=40000,
        meal_type="lunch",
        prep_time=10,
        image_url=None,
        tags=["vegetarian"],
        score=42.17,
        criteria_scores=CriteriaScores(price=20.00, preference=50.00, prep_time=66.67),
        reasons=[
            "Phù hợp với 1/2 sở thích đã chọn",
            "Giá 40.000đ nằm trong ngân sách 50.000đ",
        ],
    ),
]

def build_mock_response(payload: DecisionRecommendRequest) -> DecisionResponse:
    # Chỉ lọc theo giá để Frontend test được empty state (budget_max < 20000)
    items = [i for i in MOCK_ITEMS if i.price <= payload.budget_max][:payload.limit]
    if payload.weights is not None:
        scoring = ScoringResponse(
            weights=ScoringWeights(
                price=payload.weights.price,
                preference=payload.weights.preference,
                prep_time=payload.weights.prep_time,
            )
        )
    else:
        scoring = ScoringResponse()

    return DecisionResponse(
        items=items,
        total=len(items),
        limit=payload.limit,
        applied_filters=AppliedFilters(
            budget_max=payload.budget_max,
            meal_type=payload.meal_type,
            max_prep_time=payload.max_prep_time,
            excluded_ingredients=payload.excluded_ingredients,
            preferred_tags=payload.preferred_tags,
        ),
        scoring=scoring,
    )