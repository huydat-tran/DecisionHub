"""Xếp hạng ứng viên theo tổng điểm WSM (Bước 5 - Ranking) cho Decision Engine.

Nhận danh sách ứng viên đã có trường `score` từ calculator.py,
sắp xếp giảm dần và xử lý tie-break ổn định. Không tính lại WSM.

Thứ tự tie-break:
  1. Tổng điểm giảm dần (score cao hơn đứng trước).
  2. Chi phí tăng dần (price hoặc estimated_cost thấp hơn đứng trước).
  3. Tên tăng dần A-Z (name).
  4. ID tăng dần (id).
  5. Nếu tất cả bằng nhau → giữ nguyên thứ tự ban đầu (stable sort của Python).
"""

from typing import Any

# Các tên trường chi phí được nhận diện theo thứ tự ưu tiên
_COST_FIELDS: tuple[str, ...] = ("price", "estimated_cost", "cost")

# Giá trị sentinel cho tie-break khi trường chi phí bị thiếu
# (ứng viên thiếu chi phí bị xếp sau ứng viên có chi phí)
_MISSING_COST: float = float("inf")

# Giá trị sentinel cho tên và ID khi bị thiếu
_MISSING_NAME: str = ""
_MISSING_ID: int = 2**63 - 1  # int lớn nhất thực tế


def _get_cost(candidate: dict[str, Any]) -> float:
    """Lấy giá trị chi phí từ ứng viên; trả _MISSING_COST nếu thiếu."""
    for field in _COST_FIELDS:
        val = candidate.get(field)
        if val is not None:
            try:
                cost = float(val)
                if cost == cost:  # loại NaN
                    return cost
            except (TypeError, ValueError):
                pass
    return _MISSING_COST


def _get_name(candidate: dict[str, Any]) -> str:
    """Lấy tên ứng viên để tie-break; trả chuỗi rỗng nếu thiếu."""
    return str(candidate.get("name") or _MISSING_NAME).lower()


def _get_id(candidate: dict[str, Any]) -> int:
    """Lấy ID ứng viên để tie-break; trả sentinel lớn nếu thiếu."""
    val = candidate.get("id")
    if val is None:
        return _MISSING_ID
    try:
        return int(val)
    except (TypeError, ValueError):
        return _MISSING_ID


def _sort_key(item: tuple[int, dict[str, Any]]) -> tuple[float, float, str, int]:
    """Khóa sắp xếp: (score giảm dần, cost tăng dần, name tăng dần, id tăng dần)."""
    _original_idx, cand = item
    score = cand.get("score", 0.0)
    try:
        score = float(score)
    except (TypeError, ValueError):
        score = 0.0
    return (-score, _get_cost(cand), _get_name(cand), _get_id(cand))


def rank_candidates(
    candidates: list[dict[str, Any]],
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Sắp xếp ứng viên theo điểm WSM giảm dần với tie-break ổn định.

    Args:
        candidates: Danh sách ứng viên đã có trường `score` từ calculator.py.
        limit: Số lượng kết quả tối đa trả về (None = trả tất cả).

    Returns:
        Danh sách ứng viên đã sắp xếp, mỗi phần tử có thêm trường `rank` (1-based).
        Không mutate dict đầu vào.
    """
    if not candidates:
        return []

    # Đánh chỉ số ban đầu để stable sort khi tất cả tiêu chí bằng nhau
    indexed = list(enumerate(candidates))
    sorted_indexed = sorted(indexed, key=_sort_key)

    results: list[dict[str, Any]] = []
    for rank, (_original_idx, cand) in enumerate(sorted_indexed, start=1):
        out = dict(cand)
        out["rank"] = rank
        results.append(out)

    if limit is not None and limit > 0:
        results = results[:limit]

    return results
