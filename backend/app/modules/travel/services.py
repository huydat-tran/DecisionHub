"""Dịch vụ gợi ý địa điểm du lịch (Travel Recommendation Service).

Điều phối: Repository -> Adapter -> Decision Engine -> Trả kết quả xếp hạng.
"""

import logging
from typing import Any

from sqlalchemy.orm import Session

from .repository import get_active_travel_places
from app.modules.decision.engine.pipeline import evaluate_decision
from app.modules.travel.adapter import (
    adapt_travel_candidates,
    adapt_travel_criteria,
)
from app.modules.travel.schemas import (
    RecommendedTravelResponse,
    TravelAppliedFilters,
    TravelDecisionData,
    TravelExcludedOptionResponse,
    TravelRecommendRequest,
    TravelScoringResponse,
)

logger = logging.getLogger(__name__)


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


def recommend_travel(
    db: Session,
    payload: TravelRecommendRequest,
) -> tuple[TravelDecisionData, str]:
    """Thực thi pipeline gợi ý địa điểm du lịch qua Decision Engine chung."""
    raw_candidates = get_active_travel_places(db)

    # 1. Chuyển đổi dữ liệu sang schema Engine chung
    adapted_candidates = adapt_travel_candidates(
        raw_candidates,
        preferred_activities=payload.preferred_activities,
    )
    adapted_criteria = adapt_travel_criteria()

    # 2. Lọc điều kiện cứng (Hard Constraints) ngân sách, thời lượng, khu vực
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

    # 3. Chạy Decision Engine pipeline nếu còn ứng viên hợp lệ
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

    # 4. Chuẩn hóa kết quả đề xuất và tạo lý do giải thích
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

    # 5. Đóng gói response data
    weights_dict = {c["field_name"]: c["weight"] for c in adapted_criteria}
    region_str = payload.region.value if payload.region is not None else None
    decision_data = TravelDecisionData(
        items=items,
        excluded_items=excluded_items,
        total=len(valid_candidates),
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
