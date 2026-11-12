def calculate_price_score(price: float | int, budget_max: float | int) -> float:
    """Tính điểm tiêu chí Giá (COST: càng thấp càng tốt).

    Công thức: 100 * (1 - price / budget_max), giới hạn trong [0, 100].
    """
    if budget_max <= 0:
        return 0.0
    return max(0.0, min(100.0, 100.0 * (1.0 - price / budget_max)))


def calculate_preference_score(
    food_tags: list[str] | set[str] | None,
    preferred_tags: list[str] | None,
) -> float:
    """Tính điểm tiêu chí Sở thích (BENEFIT: khớp càng nhiều càng tốt).

    - Nếu không có preferred_tags: mặc định 50.0 (trung tính).
    - So khớp không phân biệt hoa thường.
    - Điểm = 100 * số tag khớp / tổng tag người dùng chọn.
    """
    if not preferred_tags:
        return 50.0

    # Chuẩn hóa lowercase và loại bỏ trùng lặp
    pref_set = {t.lower().strip() for t in preferred_tags if t}
    if not pref_set:
        return 50.0

    food_set = {t.lower().strip() for t in (food_tags or []) if t}
    matched = sum(1 for tag in pref_set if tag in food_set)

    return 100.0 * matched / len(pref_set)


def calculate_prep_time_score(
    prep_time: int | None,
    max_prep_time: int | None,
) -> float:
    """Tính điểm tiêu chí Thời gian chuẩn bị (COST: càng nhanh càng tốt).

    - Nếu không đặt max_prep_time hoặc món không có prep_time: mặc định 50.0.
    - Công thức: 100 * (1 - prep_time / max_prep_time), giới hạn trong [0, 100].
    """
    if max_prep_time is None or prep_time is None:
        return 50.0

    if max_prep_time <= 0:
        return 0.0

    return max(0.0, min(100.0, 100.0 * (1.0 - prep_time / max_prep_time)))


def calculate_total_score(
    price_score: float,
    preference_score: float,
    prep_time_score: float,
) -> float:
    """Tính tổng điểm WSM: (0.40 * price) + (0.35 * preference) + (0.25 * prep_time).

    Giữ nguyên số thực float cho bước ranking, chỉ làm tròn khi serialize.
    """
    return (
        0.40 * price_score
        + 0.35 * preference_score
        + 0.25 * prep_time_score
    )
