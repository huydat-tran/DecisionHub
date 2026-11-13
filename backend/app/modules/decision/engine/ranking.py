"""Decision Engine – Ranking (Bước 4).

Triển khai Bước 4 trong pipeline 6 bước của DecisionHub:
  - Sắp xếp danh sách ứng viên đã được tính điểm WSM theo thứ tự giảm dần.
  - Tie-breaker: chi phí thấp hơn → ưu tiên hơn; nếu vẫn bằng → tên/ID.
  - Giới hạn kết quả trả về theo tham số top_n.

Quy tắc:
  - Engine không truy vấn database.
  - Nhận list[dict] candidates đã có trường ``score`` và field chi phí.
"""

from __future__ import annotations


def rank_candidates(
    candidates: list[dict],
    top_n: int = 5,
    cost_key: str = "cost",
    name_key: str = "name",
) -> list[dict]:
    """Xếp hạng và cắt danh sách ứng viên theo điểm WSM.

    Tie-breaker (theo thứ tự ưu tiên):
      1. Điểm WSM cao hơn → xếp trước.
      2. Chi phí thấp hơn (``cost_key``) → xếp trước.
      3. Tên địa điểm/món ăn theo thứ tự từ điển (``name_key``) → xếp trước.

    Args:
        candidates: Danh sách ứng viên đã có trường ``score``.
        top_n: Số lượng ứng viên trả về tối đa. Mặc định 5.
        cost_key: Key giá trị chi phí trong candidate dict (mặc định 'cost').
        name_key: Key tên trong candidate dict (mặc định 'name').

    Returns:
        Danh sách tối đa ``top_n`` ứng viên đã được sắp xếp.
    """
    if not candidates:
        return []

    sorted_candidates = sorted(
        candidates,
        key=lambda c: (
            -c.get("score", 0),          # 1. Điểm giảm dần
            c.get(cost_key, 0),          # 2. Chi phí tăng dần (thấp hơn ưu tiên)
            c.get(name_key, ""),         # 3. Tên theo alphabet
        ),
    )

    return sorted_candidates[:top_n]
