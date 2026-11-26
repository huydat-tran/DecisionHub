"""Logic gợi ý địa điểm du lịch (Travel Recommendation Logic).

Chứa bước chuyển đổi ứng viên, lọc điều kiện cứng và chấm điểm/xếp hạng
qua Decision Engine. Không truy vấn CSDL và không đóng gói response hiển thị.
"""

from typing import Any

from app.modules.decision.engine.pipeline import evaluate_decision
from app.modules.travel.adapter import (
    adapt_travel_candidates,
    adapt_travel_criteria,
)
from app.modules.travel.schemas import (
    TravelExcludedOptionResponse,
    TravelRecommendRequest,
)


def _format_vnd(amount: int) -> str:
    return f"{amount:,}".replace(",", ".") + "đ"


def evaluate_travel_recommendation(
    raw_candidates: list[Any],
    payload: TravelRecommendRequest,
) -> tuple[list[dict[str, Any]], int, list[TravelExcludedOptionResponse], list[dict[str, Any]]]:
    """Lọc điều kiện cứng và chạy Decision Engine cho danh sách ứng viên Travel.

    Returns:
        (ranked_candidates, total_valid, excluded_items, adapted_criteria)
    """
    adapted_candidates = adapt_travel_candidates(
        raw_candidates,
        preferred_activities=payload.preferred_activities,
    )
    adapted_criteria = adapt_travel_criteria()

    valid_candidates: list[dict[str, Any]] = []
    excluded_items: list[TravelExcludedOptionResponse] = []

    for cand in adapted_candidates:
        reasons: list[str] = []
        cost = int(cand.get("estimated_cost") or 0)
        duration = float(cand.get("estimated_duration") or 0.0)

        if payload.budget_max is not None and cost > payload.budget_max:
            reasons.append(
                f"Chi phí {_format_vnd(cost)} vượt quá ngân sách tối đa {_format_vnd(payload.budget_max)}."
            )
        if payload.max_duration is not None and duration > payload.max_duration:
            reasons.append(
                f"Thời lượng {duration:.1f}h vượt quá thời lượng tối đa {payload.max_duration:.1f}h."
            )
        if payload.region is not None:
            reg_val = payload.region.value
            if cand.get("region") != reg_val:
                reasons.append(
                    f"Khu vực '{cand.get('region')}' không khớp khu vực yêu cầu '{reg_val}'."
                )
        if payload.activity_type is not None and payload.activity_type.strip():
            act_req = payload.activity_type.strip()
            if cand.get("activity_type") != act_req:
                reasons.append(
                    f"Loại hình '{cand.get('activity_type')}' không khớp loại hình yêu cầu '{act_req}'."
                )

        if reasons:
            excluded_items.append(
                TravelExcludedOptionResponse(
                    id=cand.get("id"),
                    name=str(cand.get("name") or ""),
                    status="excluded",
                    is_excluded=True,
                    exclusion_reason="; ".join(reasons),
                    exclusion_reasons=reasons,
                )
            )
        else:
            valid_candidates.append(cand)

    if valid_candidates:
        eval_result = evaluate_decision(
            candidates=valid_candidates,
            criteria=adapted_criteria,
            domain="travel",
            user_preferences=payload.preferred_activities,
            limit=payload.limit,
        )
        ranked_candidates = eval_result.get("valid_candidates", [])
    else:
        ranked_candidates = []

    return ranked_candidates, len(valid_candidates), excluded_items, adapted_criteria
