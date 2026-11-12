def rank_foods(foods: list[dict], limit: int = 5) -> list[dict]:
    """Xếp hạng các món ăn theo thuật toán WSM và tie-breaker quy định tại API Contract A4:

    1. Điểm tổng (score) cao hơn xếp trước (giữ số thực để xếp hạng).
    2. Tie-breaker 1: Giá thấp hơn đứng trước.
    3. Tie-breaker 2: Thời gian chuẩn bị thấp hơn đứng trước (an toàn với None).
    4. Tie-breaker 3: food_id tăng dần.
    """
    sorted_foods = sorted(
        foods,
        key=lambda food: (
            -food.get("score", food.get("total_score", 0.0)),
            food.get("price", 0),
            food.get("prep_time") if food.get("prep_time") is not None else float("inf"),
            food.get("food_id", 0),
        ),
    )

    # Giới hạn số lượng kết quả trả về theo limit đã định
    return sorted_foods[: max(0, limit)]
