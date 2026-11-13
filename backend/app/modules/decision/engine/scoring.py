"""Chuẩn hóa tiêu chí và tính điểm WSM dùng chung cho mọi domain.

Score(A) = Σ (wᵢ × sᵢ(A)), với sᵢ trong khoảng 0–100.
Engine không chứa công thức riêng cho Food hay Travel.
"""

from decimal import Decimal, ROUND_HALF_UP

_SCORE_QUANTUM = Decimal("0.01")


def _decimal(value: object) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def normalize(value: object, low: object, high: object, direction: str) -> Decimal:
    """Đưa một giá trị thô về thang 0–100 theo direction min hoặc max.

    Khi mọi ứng viên bằng nhau, điểm chuẩn hóa là 100.
    """
    if direction not in ("min", "max"):
        raise ValueError(f"Direction không hợp lệ: {direction}")

    current = _decimal(value)
    minimum = _decimal(low)
    maximum = _decimal(high)
    if maximum == minimum:
        return Decimal("100")

    span = maximum - minimum
    if direction == "min":
        ratio = (Decimal(1) - (current - minimum) / span) * Decimal(100)
    else:
        ratio = ((current - minimum) / span) * Decimal(100)
    return ratio


def _quantize(score: Decimal) -> float:
    return float(score.quantize(_SCORE_QUANTUM, rounding=ROUND_HALF_UP))


def score_candidates(candidates: list[dict], criteria: list) -> list[dict]:
    """Chấm điểm danh sách ứng viên bằng các tiêu chí đã được lọc theo domain."""
    if not candidates:
        return []

    bounds: dict[str, tuple[Decimal, Decimal]] = {}
    for criterion in criteria:
        raw_values = []
        for candidate in candidates:
            values = candidate.get("values") or {}
            if criterion.name not in values:
                raise ValueError(
                    f"Ứng viên '{candidate.get('name')}' thiếu giá trị tiêu chí '{criterion.name}'"
                )
            raw_values.append(_decimal(values[criterion.name]))
        bounds[criterion.name] = (min(raw_values), max(raw_values))

    scored: list[dict] = []
    for candidate in candidates:
        details: dict[str, float] = {}
        total = Decimal(0)
        for criterion in criteria:
            low, high = bounds[criterion.name]
            normalized = normalize(
                candidate["values"][criterion.name],
                low,
                high,
                criterion.direction,
            )
            weight = _decimal(criterion.weight)
            details[criterion.name] = _quantize(normalized)
            total += normalized * weight
        scored.append(
            {
                "id": candidate.get("id"),
                "name": candidate.get("name"),
                "tie_cost": candidate.get("tie_cost"),
                "score": _quantize(total),
                "criteria_scores": details,
            }
        )
    return scored
