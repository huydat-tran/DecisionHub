"""Dịch vụ hiển thị và đóng gói dữ liệu gợi ý địa điểm du lịch (Travel Display Service)."""

from typing import Any

from app.modules.travel.schemas import (
    RecommendedTravelResponse,
    TravelAppliedFilters,
    TravelDecisionData,
    TravelExcludedOptionResponse,
    TravelRecommendRequest,
    TravelScoringResponse,
)


def _format_vnd(amount: int) -> str:
    """Format số tiền VND sang định dạng hiển thị (vd: 500000 -> '500.000đ')."""
    return f"{amount:,}".replace(",", ".") + "đ"


def _build_travel_reasons(
    cand: dict[str, Any],
    payload: TravelRecommendRequest,
) -> list[str]:
    """Sinh 1-3 lý do gợi ý dựa trên dữ liệu thực tế và điều kiện đầu vào của người dùng."""
    reasons: list[str] = []
    cost = int(cand.get("estimated_cost", 0))
    duration = float(cand.get("estimated_duration", 0.0))

    # 1. Lý do Chi phí
    if cost == 0:
        reasons.append("Chi phí 0đ, tối ưu ngân sách")
    elif payload.budget_max is not None:
        reasons.append(
            f"Chi phí {_format_vnd(cost)} nằm trong ngân sách tối đa {_format_vnd(payload.budget_max)}"
        )
    else:
        reasons.append(f"Chi phí tham khảo: {_format_vnd(cost)}")

    # 2. Lý do Thời lượng
    if payload.max_duration is not None:
        reasons.append(
            f"Thời lượng {duration:.1f}h phù hợp giới hạn {payload.max_duration:.1f}h"
        )
    else:
        reasons.append(f"Thời lượng trải nghiệm ước tính: {duration:.1f}h")

    # 3. Lý do Hoạt động / Sở thích
    matched = cand.get("matched_activities") or []
    if matched:
        reasons.append(f"Phù hợp sở thích / hoạt động: {', '.join(matched[:3])}")
    elif cand.get("highlights"):
        reasons.append(f"Có {len(cand['highlights'])} hoạt động trải nghiệm nổi bật")
    elif cand.get("activity_type"):
        reasons.append(f"Loại hình trải nghiệm: {cand['activity_type']}")

    return reasons[:3]


def build_travel_decision_response(
    ranked_candidates: list[dict[str, Any]],
    total_valid: int,
    excluded_items: list[TravelExcludedOptionResponse],
    adapted_criteria: list[dict[str, Any]],
    payload: TravelRecommendRequest,
) -> tuple[TravelDecisionData, str]:
    """Đóng gói kết quả gợi ý thành dữ liệu hiển thị TravelDecisionData và thông báo."""
    items: list[RecommendedTravelResponse] = []
    for cand in ranked_candidates:
        reasons = _build_travel_reasons(cand, payload)
        dest_id = int(cand.get("destination_id") or cand.get("id") or 0)
        items.append(
            RecommendedTravelResponse(
                destination_id=dest_id,
                name=str(cand.get("name") or ""),
                province_city=str(cand.get("province_city") or ""),
                region=str(cand.get("region") or ""),
                estimated_cost=int(cand.get("estimated_cost") or 0),
                estimated_duration=float(cand.get("estimated_duration") or 0.0),
                activity_type=str(cand.get("activity_type") or ""),
                highlights=list(cand.get("highlights") or []),
                description=cand.get("description"),
                image_url=cand.get("image_url"),
                rating=cand.get("rating"),
                score=float(cand.get("score") or 0.0),
                total_score=float(cand.get("total_score") or cand.get("score") or 0.0),
                rank=int(cand.get("rank") or 1),
                criteria_scores=dict(cand.get("criteria_scores") or {}),
                criteria_details=dict(cand.get("criteria_details") or {}),
                reasons=reasons,
                id=dest_id,
            )
        )

    weights_dict = {c["field_name"]: c["weight"] for c in adapted_criteria}
    region_str = payload.region.value if payload.region is not None else None
    decision_data = TravelDecisionData(
        items=items,
        excluded_items=excluded_items,
        total=total_valid,
        total_excluded=len(excluded_items),
        limit=payload.limit,
        applied_filters=TravelAppliedFilters(
            budget_max=payload.budget_max,
            max_duration=payload.max_duration,
            region=region_str,
            activity_type=payload.activity_type,
            preferred_activities=payload.preferred_activities,
        ),
        scoring=TravelScoringResponse(
            method="WSM",
            weights=weights_dict,
        ),
    )

    if not items:
        message = (
            "Không có địa điểm nào thỏa mãn toàn bộ điều kiện. "
            "Hãy thử tăng ngân sách tối đa hoặc nới thời lượng."
        )
    else:
        message = f"Đề xuất {len(items)} địa điểm du lịch phù hợp nhất."

    return decision_data, message
