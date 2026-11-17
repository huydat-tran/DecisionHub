"""Decision Engine dùng chung cho Food và Travel."""

from typing import Any

from app.modules.decision.engine.calculator import (
    CriteriaScoresResult,
    FoodWSMResult,
    calculate_food_wsm,
    calculate_preference_score,
    calculate_prep_time_score,
    calculate_price_score,
    calculate_wsm_score,
)
from app.modules.decision.engine.filters import (
    filter_candidates,
    passes_hard_constraints,
)

__all__ = [
    "CriteriaScoresResult",
    "FoodWSMResult",
    "calculate_food_wsm",
    "calculate_preference_score",
    "calculate_prep_time_score",
    "calculate_price_score",
    "calculate_wsm_score",
    "evaluate",
    "filter_candidates",
    "passes_hard_constraints",
]


def __getattr__(name: str) -> Any:
    if name == "evaluate":
        from app.modules.decision.engine.pipeline import evaluate

        return evaluate
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
