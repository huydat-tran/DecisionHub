"""Decision Engine – Scoring & Explanation.

Triển khai 2 bước trong pipeline 6 bước của DecisionHub:
  - Bước 3: Criteria Scoring (0–100, min/max direction)
  - Bước 5: Explanation (1–3 lý do dựa trên dữ liệu thực)

Quy tắc:
  - Engine không truy vấn database; nhận list[dict] ứng viên đã chuẩn hóa.
  - Mỗi tiêu chí được chuẩn hóa về thang 0–100 trước khi nhân weight.
  - Bước Weighted Sum Model (WSM): Score(A) = Σ(wᵢ × sᵢ(A)).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass
class Criterion:
    """Mô tả một tiêu chí chấm điểm."""

    key: str                       # key tương ứng trong candidate dict
    name: str                      # tên hiển thị trong explanation
    direction: Literal["min", "max"]
    weight: float                  # 0 < weight ≤ 1; tổng các weight phải = 1


def _normalize(value: float, min_val: float, max_val: float, direction: Literal["min", "max"]) -> float:
    """Chuẩn hóa một giá trị về thang 0–100.

    Args:
        value: Giá trị cần chuẩn hóa.
        min_val: Giá trị nhỏ nhất trong tập ứng viên.
        max_val: Giá trị lớn nhất trong tập ứng viên.
        direction: 'min' → thấp hơn tốt hơn; 'max' → cao hơn tốt hơn.

    Returns:
        Điểm đã chuẩn hóa trong [0, 100].
        Nếu min_val == max_val (tất cả ứng viên bằng nhau) → trả về 100.
    """
    if max_val == min_val:
        return 100.0
    ratio = (value - min_val) / (max_val - min_val)
    if direction == "min":
        return round((1.0 - ratio) * 100, 4)
    return round(ratio * 100, 4)


def score_candidates(
    candidates: list[dict],
    criteria: list[Criterion],
) -> list[dict]:
    """Tính điểm WSM cho danh sách ứng viên đã qua lọc hard constraints.

    Bổ sung vào mỗi candidate:
      - ``criteria_scores``: dict {key: điểm_0_100} cho từng tiêu chí.
      - ``score``: điểm tổng WSM (0–100), làm tròn 2 chữ số thập phân.

    Args:
        candidates: Danh sách ứng viên (mỗi phần tử là dict có các key của criteria).
        criteria: Danh sách Criterion định nghĩa cách chấm điểm.

    Returns:
        Danh sách candidate đã được bổ sung ``score`` và ``criteria_scores``.
        Nếu danh sách rỗng → trả về rỗng ngay.
    """
    if not candidates:
        return []

    # --- Bước 3: Criteria Scoring ---
    for crit in criteria:
        values = [float(c[crit.key]) for c in candidates]
        min_val, max_val = min(values), max(values)
        for c in candidates:
            raw = float(c[crit.key])
            c.setdefault("criteria_scores", {})[crit.key] = _normalize(raw, min_val, max_val, crit.direction)

    # --- WSM: Score(A) = Σ(wᵢ × sᵢ(A)) ---
    for c in candidates:
        wsm = sum(
            c["criteria_scores"][crit.key] * crit.weight
            for crit in criteria
        )
        c["score"] = round(wsm, 2)

    return candidates


def build_explanations(
    candidate: dict,
    criteria: list[Criterion],
    applied_filters: dict,
) -> list[str]:
    """Sinh 1–3 lý do giải thích cho ứng viên dựa trên dữ liệu thực.

    Quy tắc:
      - Chọn tối đa 3 tiêu chí có điểm normalized cao nhất.
      - Lý do gắn với giá trị thực, không bịa.
      - Mỗi domain tự truyền ``applied_filters`` phù hợp.

    Args:
        candidate: Ứng viên đã được tính điểm.
        criteria: Danh sách Criterion.
        applied_filters: Bộ lọc người dùng đã áp dụng (dùng để so sánh trong câu).

    Returns:
        Danh sách tối đa 3 chuỗi lý do.
    """
    scores = candidate.get("criteria_scores", {})
    # Sắp xếp theo điểm giảm dần, lấy top 3
    top_criteria = sorted(criteria, key=lambda c: scores.get(c.key, 0), reverse=True)[:3]

    reasons: list[str] = []
    for crit in top_criteria:
        score = scores.get(crit.key, 0)
        raw_value = candidate.get(crit.key)
        if raw_value is None:
            continue
        reasons.append(_format_reason(crit, raw_value, score, applied_filters))

    return reasons


def _format_reason(crit: Criterion, raw_value: float, score: float, filters: dict) -> str:
    """Tạo câu giải thích cho một tiêu chí dựa trên key."""
    # --- Travel ---
    if crit.key == "cost":
        budget = filters.get("budget_max")
        formatted = f"{int(raw_value):,}".replace(",", ".")
        if budget:
            budget_fmt = f"{int(budget):,}".replace(",", ".")
            return f"Chi phí {formatted} VND nằm trong ngân sách {budget_fmt} VND (điểm: {score:.0f}/100)"
        return f"Chi phí {formatted} VND (điểm: {score:.0f}/100)"

    if crit.key == "duration":
        max_dur = filters.get("max_duration")
        if max_dur:
            return (
                f"Thời lượng {raw_value:.1f} giờ phù hợp với quỹ thời gian "
                f"{max_dur:.1f} giờ (điểm: {score:.0f}/100)"
            )
        return f"Thời lượng trải nghiệm {raw_value:.1f} giờ (điểm: {score:.0f}/100)"

    if crit.key == "preference":
        pref = filters.get("preferred_activity")
        if pref:
            return f"Phù hợp loại hình '{pref}' bạn ưa thích (điểm: {score:.0f}/100)"
        return f"Điểm đánh giá chất lượng cao (điểm: {score:.0f}/100)"

    # --- Food ---
    if crit.key == "price":
        budget = filters.get("budget_max")
        formatted = f"{int(raw_value):,}".replace(",", ".")
        if budget:
            budget_fmt = f"{int(budget):,}".replace(",", ".")
            return f"Giá {formatted} VND trong ngân sách {budget_fmt} VND (điểm: {score:.0f}/100)"
        return f"Giá {formatted} VND (điểm: {score:.0f}/100)"

    if crit.key == "prep_time":
        max_pt = filters.get("max_prep_time")
        if max_pt:
            return f"Thời gian chuẩn bị {int(raw_value)} phút ≤ {int(max_pt)} phút (điểm: {score:.0f}/100)"
        return f"Thời gian chuẩn bị {int(raw_value)} phút (điểm: {score:.0f}/100)"

    # Fallback generic
    return f"{crit.name}: điểm {score:.0f}/100"
