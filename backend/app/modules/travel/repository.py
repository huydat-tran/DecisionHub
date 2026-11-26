"""Travel data access layer.

Queries active travel places from the database.
Falls back to mock data when the DB returns no rows or raises an error.
"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.travel.models import TravelPlace
from app.modules.travel.mock_data import RAW_MOCK_TRAVEL_CANDIDATES


def get_active_travel_places(db: Session) -> list[Any]:
    """Return active travel places from DB; fallback to mock dicts if empty."""
    try:
        stmt = (
            select(TravelPlace)
            .where(TravelPlace.is_active.is_(True), TravelPlace.estimated_cost >= 0)
            .order_by(TravelPlace.id.asc())
        )
        places = list(db.scalars(stmt).all())
        if places:
            return places
    except Exception:  # pragma: no cover
        pass
    return list(RAW_MOCK_TRAVEL_CANDIDATES)
