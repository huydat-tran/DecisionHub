"""Module Travel: Địa điểm du lịch và gợi ý thông minh."""

from app.modules.travel.adapter import (
    DEFAULT_TRAVEL_CRITERIA,
    DEFAULT_TRAVEL_WEIGHTS,
    adapt_travel_candidate,
    adapt_travel_candidates,
    adapt_travel_criteria,
)
from app.modules.travel.models import Destination, TravelPlace, TravelRegion

__all__ = [
    "DEFAULT_TRAVEL_CRITERIA",
    "DEFAULT_TRAVEL_WEIGHTS",
    "Destination",
    "TravelPlace",
    "TravelRegion",
    "adapt_travel_candidate",
    "adapt_travel_candidates",
    "adapt_travel_criteria",
]
