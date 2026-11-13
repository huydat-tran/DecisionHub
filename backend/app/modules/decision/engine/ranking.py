"""Xếp hạng kết quả đã chấm điểm.

Hòa điểm: ưu tiên tie_cost thấp hơn, sau đó tên, rồi id.
"""


def _tie_cost_key(item: dict) -> tuple:
    tie_cost = item.get("tie_cost")
    if tie_cost is None:
        return (1, 0.0)
    return (0, float(tie_cost))


def rank_candidates(scored: list[dict]) -> list[dict]:
    """Sắp xếp giảm dần theo điểm tổng và gán rank bắt đầu từ 1."""
    ordered = sorted(
        scored,
        key=lambda item: (
            -float(item["score"]),
            _tie_cost_key(item),
            str(item.get("name") or ""),
            str(item.get("id") or ""),
        ),
    )
    ranked: list[dict] = []
    for index, item in enumerate(ordered, start=1):
        ranked.append({**item, "rank": index})
    return ranked
