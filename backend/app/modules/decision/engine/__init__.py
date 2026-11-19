"""Decision Engine dùng chung cho Food và Travel."""

from typing import Any

from app.modules.decision.engine.calculator import (
    CriteriaScoresResult,
    FoodWSMResult,
    calculate_food_wsm,
    calculate_preference_score,
    calculate_prep_time_score,
    calculate_price_score,
    calculate_wsm,
    calculate_wsm_score,
    validate_weights,
)
from app.modules.decision.engine.filters import (
    Constraints,
    filter_candidates,
    passes_hard_constraints,
)
from app.modules.decision.engine.ranking import rank_candidates
from app.modules.decision.engine.scoring import (
    EQUAL_RANGE_SCORE,
    NEUTRAL_PREFERENCE_SCORE,
    normalize_benefit,
    normalize_cost,
    normalize_value,
    score_candidates,
    score_criterion,
    score_preference,
)

__all__ = [
    "EQUAL_RANGE_SCORE",
    "NEUTRAL_PREFERENCE_SCORE",
    "Constraints",
    "CriteriaScoresResult",
    "FoodWSMResult",
    "calculate_food_wsm",
    "calculate_preference_score",
    "calculate_prep_time_score",
    "calculate_price_score",
    "calculate_wsm",
    "calculate_wsm_score",
    "evaluate",
    "filter_candidates",
    "normalize_benefit",
    "normalize_cost",
    "normalize_value",
    "passes_hard_constraints",
    "rank_candidates",
    "score_candidates",
    "score_criterion",
    "score_preference",
    "validate_weights",
]


def __getattr__(name: str) -> Any:
    if name == "evaluate":
        from app.modules.decision.engine.pipeline import evaluate

        return evaluate
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
