"""Service cho module Travel.

Triển khai các nghiệp vụ:
  1. Quick Search (tìm kiếm nhanh kết hợp lọc chip)
  2. Get Place Detail (lấy chi tiết địa điểm)
  3. Recommend (áp dụng Constraint Filtering -> Scoring WSM -> Ranking -> Explanation)
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.common.exceptions import ResourceNotFoundException
from app.modules.decision.engine.calculator import (
    Criterion,
    build_explanations,
    score_candidates,
)
from app.modules.decision.engine.ranking import rank_candidates
from app.modules.travel.models import TravelPlace
from app.modules.travel.repository import (
    get_active_places,
    get_place_by_id,
    search_places,
)
from app.modules.travel.schemas import (
    TravelAppliedFilters,
    TravelCriteriaScores,
    TravelDecisionResponse,
    TravelPlaceDetail,
    TravelQuickSearchItem,
    TravelRecommendedItem,
    TravelRecommendRequest,
    TravelScoringResponse,
    TravelScoringWeights,
)

# Rubric Travel đã thống nhất:
# cost 40% (min), preference 35% (max), duration 25% (min)
TRAVEL_CRITERIA = [
    Criterion(
        key="cost",
        name="Chi phí du lịch",
        direction="min",
        weight=0.40,
    ),
    Criterion(
        key="preference",
        name="Mức phù hợp sở thích",
        direction="max",
        weight=0.35,
    ),
    Criterion(
        key="duration",
        name="Thời lượng trải nghiệm",
        direction="min",
        weight=0.25,
    ),
]


def _calculate_preference_raw(place: TravelPlace, preferred_activity: str | None) -> float:
    """Tính giá trị preference thô (0–100) kết hợp giữa rating và khớp activity_type.

    Công thức theo thiết kế đã duyệt (α = 0.5):
      rating_component = rating * 20 (thang 1.0-5.0 -> 20-100)
      Nếu không truyền preferred_activity: lấy 100% rating_component
      Nếu có preferred_activity: 0.5 * rating_component + 0.5 * (100 nếu khớp else 0)
    """
    rating_val = float(place.rating) if place.rating is not None else 4.0
    rating_score = max(0.0, min(100.0, rating_val * 20.0))

    if not preferred_activity:
        return rating_score

    is_match = 100.0 if place.activity_type.strip().lower() == preferred_activity.strip().lower() else 0.0
    return round(0.5 * rating_score + 0.5 * is_match, 2)


def get_travel_recommendations(
    db: Session,
    request: TravelRecommendRequest,
) -> TravelDecisionResponse:
    """Quy trình gợi ý địa điểm du lịch bằng pipeline Decision Engine.

    Bước 1: Candidate Retrieval (lấy các travel_places active)
    Bước 2: Constraint Filtering (lọc ngân sách, thời lượng, khu vực)
    Bước 3: Criteria Scoring (chuẩn hóa min/max theo rubric)
    Bước 4: Weighted Sum Model (WSM)
    Bước 5: Ranking (top N, tie-breaker)
    Bước 6: Explanation (lý do thực tế)
    """
    # 1. Candidate Retrieval
    raw_places = get_active_places(db)

    # 2. Constraint Filtering
    valid_places: list[TravelPlace] = []
    for place in raw_places:
        cost = int(place.estimated_cost)
        duration = float(place.estimated_duration)

        # Hard constraint bắt buộc: budget_max & max_duration
        if cost > request.budget_max:
            continue
        if duration > request.max_duration:
            continue

        # Hard constraint tùy chọn: regions
        if request.regions:
            normalized_regions = [r.strip().lower() for r in request.regions]
            place_region = place.region.value.lower() if hasattr(place.region, "value") else str(place.region).lower()
            if place_region not in normalized_regions:
                continue

        valid_places.append(place)

    if not valid_places:
        return TravelDecisionResponse(
            items=[],
            total=0,
            limit=request.top_n,
            applied_filters=TravelAppliedFilters(
                budget_max=request.budget_max,
                max_duration=request.max_duration,
                regions=request.regions,
                preferred_activity=request.preferred_activity,
            ),
            scoring=TravelScoringResponse(
                method="WSM",
                weights=TravelScoringWeights(cost=0.40, preference=0.35, duration=0.25),
            ),
        )

    # Chuẩn hóa sang dict để đưa vào Decision Engine độc lập
    candidates = []
    place_map: dict[int, TravelPlace] = {}
    for p in valid_places:
        place_map[p.id] = p
        pref_val = _calculate_preference_raw(p, request.preferred_activity)
        candidates.append({
            "place_id": p.id,
            "name": p.name,
            "cost": float(p.estimated_cost),
            "duration": float(p.estimated_duration),
            "preference": pref_val,
        })

    # 3 & 4. Criteria Scoring & WSM
    scored_candidates = score_candidates(candidates, TRAVEL_CRITERIA)

    # 5. Ranking (Tie-breaker: score giảm dần -> cost tăng dần -> name alphabet)
    ranked_candidates = rank_candidates(
        scored_candidates,
        top_n=request.top_n,
        cost_key="cost",
        name_key="name",
    )

    # 6. Explanation & Format Output
    applied_filters_dict = {
        "budget_max": request.budget_max,
        "max_duration": request.max_duration,
        "preferred_activity": request.preferred_activity,
    }

    results: list[TravelRecommendedItem] = []
    for c in ranked_candidates:
        place = place_map[c["place_id"]]
        reasons = build_explanations(c, TRAVEL_CRITERIA, applied_filters_dict)
        c_scores = c.get("criteria_scores", {})

        results.append(
            TravelRecommendedItem(
                place_id=place.id,
                name=place.name,
                province_city=place.province_city,
                region=place.region.value if hasattr(place.region, "value") else str(place.region),
                estimated_cost=int(place.estimated_cost),
                estimated_duration=float(place.estimated_duration),
                activity_type=place.activity_type,
                rating=float(place.rating),
                image_url=place.image_url,
                score=c["score"],
                criteria_scores=TravelCriteriaScores(
                    cost=round(c_scores.get("cost", 0.0), 2),
                    preference=round(c_scores.get("preference", 0.0), 2),
                    duration=round(c_scores.get("duration", 0.0), 2),
                ),
                reasons=reasons,
            )
        )

    return TravelDecisionResponse(
        items=results,
        total=len(results),
        limit=request.top_n,
        applied_filters=TravelAppliedFilters(
            budget_max=request.budget_max,
            max_duration=request.max_duration,
            regions=request.regions,
            preferred_activity=request.preferred_activity,
        ),
        scoring=TravelScoringResponse(
            method="WSM",
            weights=TravelScoringWeights(cost=0.40, preference=0.35, duration=0.25),
        ),
    )


def quick_search_travel(
    db: Session,
    keyword: str | None = None,
    region: str | None = None,
    budget_max: int | None = None,
    max_duration: float | None = None,
    activity_type: str | None = None,
    limit: int = 20,
) -> list[TravelQuickSearchItem]:
    """Tìm kiếm nhanh địa điểm theo từ khóa và các bộ lọc chip."""
    places = search_places(
        db=db,
        keyword=keyword,
        region=region,
        budget_max=budget_max,
        max_duration=max_duration,
        activity_type=activity_type,
        limit=limit,
    )
    return [
        TravelQuickSearchItem(
            place_id=p.id,
            name=p.name,
            province_city=p.province_city,
            region=p.region.value if hasattr(p.region, "value") else str(p.region),
            estimated_cost=int(p.estimated_cost),
            estimated_duration=float(p.estimated_duration),
            activity_type=p.activity_type,
            image_url=p.image_url,
            rating=float(p.rating),
        )
        for p in places
    ]


def get_travel_place_detail(db: Session, place_id: int) -> TravelPlaceDetail:
    """Lấy chi tiết địa điểm du lịch theo id."""
    place = get_place_by_id(db, place_id)
    if not place:
        raise ResourceNotFoundException(resource_name="Địa điểm du lịch", resource_id=place_id)

    return TravelPlaceDetail(
        place_id=place.id,
        name=place.name,
        province_city=place.province_city,
        region=place.region.value if hasattr(place.region, "value") else str(place.region),
        estimated_cost=int(place.estimated_cost),
        estimated_duration=float(place.estimated_duration),
        activity_type=place.activity_type,
        highlights=place.highlights_list,
        description=place.description,
        image_url=place.image_url,
        rating=float(place.rating),
        is_active=place.is_active,
    )
