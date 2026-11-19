from app.modules.decision.schema import DecisionRecommendRequest

from app.modules.decision.decision_response import (
    AppliedFilters,
    CriteriaScores,
    DecisionResponse,
    RecommendedFoodResponse,
)

# Danh sách món ăn mẫu thực tế cho Decision Engine Mock
MOCK_ITEMS: list[RecommendedFoodResponse] = [
    RecommendedFoodResponse(
        food_id=101,
        name="Bún chả Hà Nội",
        price=35000,
        meal_type="lunch",
        prep_time=15,
        image_url="../assets/images/foods/buncha.jpg",
        tags=["đậm đà", "truyền thống"],
        score=63.50,
        criteria_scores=CriteriaScores(price=40.00, preference=100.00, prep_time=50.00),
        reasons=[
            "Đậm đà hương vị truyền thống, thịt nướng thơm lừng",
            "Mức giá 35.000đ nằm gọn trong ngân sách của bạn",
        ],
    ),
    RecommendedFoodResponse(
        food_id=102,
        name="Bánh mì thịt đặc biệt",
        price=25000,
        meal_type="breakfast",
        prep_time=5,
        image_url="../assets/images/foods/banhmi.jpg",
        tags=["nhanh", "giòn"],
        score=58.20,
        criteria_scores=CriteriaScores(price=70.00, preference=80.00, prep_time=90.00),
        reasons=[
            "Chuẩn bị siêu nhanh chỉ 5 phút, tiện lợi mang đi",
            "Giá 25.000đ rất tiết kiệm so với ngân sách",
        ],
    ),
    RecommendedFoodResponse(
        food_id=103,
        name="Cơm chiên đậu hũ nấm",
        price=30000,
        meal_type="lunch",
        prep_time=12,
        image_url="../assets/images/foods/comtam.jpg",
        tags=["chay", "thanh đạm"],
        score=52.80,
        criteria_scores=CriteriaScores(price=60.00, preference=70.00, prep_time=60.00),
        reasons=[
            "Món ăn thanh đạm, lành mạnh cho sức khỏe",
            "Giá 30.000đ vừa vặn cho một bữa ăn dinh dưỡng",
        ],
    ),
    RecommendedFoodResponse(
        food_id=104,
        name="Phở bò tái",
        price=45000,
        meal_type="breakfast",
        prep_time=15,
        image_url="../assets/images/foods/phobo.jpg",
        tags=["nước", "truyền thống"],
        score=49.83,
        criteria_scores=CriteriaScores(price=50.00, preference=90.00, prep_time=50.00),
        reasons=[
            "Nước dùng ngọt thanh đậm đà từ xương",
            "Phù hợp bữa sáng nóng hổi, giàu đạm",
        ],
    ),
    RecommendedFoodResponse(
        food_id=105,
        name="Lẩu mini một người",
        price=65000,
        meal_type="dinner",
        prep_time=25,
        image_url="../assets/images/foods/laumini.jpg",
        tags=["nóng", "nhiều món"],
        score=42.17,
        criteria_scores=CriteriaScores(price=30.00, preference=80.00, prep_time=40.00),
        reasons=[
            "Bữa tối ấm cúng, nhiều món ăn kèm đa dạng",
            "Mức giá hợp lý cho một set lẩu cá nhân",
        ],
    ),
]

def build_mock_response(payload: DecisionRecommendRequest) -> DecisionResponse:
    # Chỉ lọc theo giá để Frontend test được empty state (budget_max < 20000)
    items = [i for i in MOCK_ITEMS if i.price <= payload.budget_max][:payload.limit]
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
        )
    )