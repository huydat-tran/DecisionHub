"""Module Travel: Địa điểm du lịch và gợi ý thông minh."""

from app.modules.travel.adapter import (
    DEFAULT_TRAVEL_CRITERIA,
    DEFAULT_TRAVEL_WEIGHTS,
    adapt_travel_candidate,
    adapt_travel_candidates,
    adapt_travel_criteria,
)
from app.modules.travel.models import Destination, TravelPlace, TravelRegion
from app.modules.travel.schemas import (
    RecommendedTravelResponse,
    TravelAppliedFilters,
    TravelDecisionData,
    TravelRecommendRequest,
    TravelRecommendResponse,
    TravelScoringResponse,
)

__all__ = [
    "DEFAULT_TRAVEL_CRITERIA",
    "DEFAULT_TRAVEL_WEIGHTS",
    "Destination",
    "RecommendedTravelResponse",
    "TravelAppliedFilters",
    "TravelDecisionData",
    "TravelPlace",
    "TravelRecommendRequest",
    "TravelRecommendResponse",
    "TravelRegion",
    "TravelScoringResponse",
    "adapt_travel_candidate",
    "adapt_travel_candidates",
    "adapt_travel_criteria",
]
