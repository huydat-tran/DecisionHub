from typing import Literal
from pydantic import BaseModel, Field


class CriteriaScores(BaseModel):
    price: float
    preference: float
    prep_time: float


class AppliedFilters(BaseModel):
    budget_max: int
    meal_type: str | None = None
    max_prep_time: int | None = None
    excluded_ingredients: list[str] = Field(default_factory=list)
    preferred_tags: list[str] = Field(default_factory=list)


class RecommendedFoodResponse(BaseModel):
    food_id: int
    name: str
    price: int
    meal_type: str
    prep_time: int
    image_url: str | None = None
    tags: list[str] = Field(default_factory=list)
    score: float = Field(ge=0, le=100)
    criteria_scores: CriteriaScores
    reasons: list[str] = Field(default_factory=list)


class ScoringWeights(BaseModel):
    price: float = 0.40
    preference: float = 0.35
    prep_time: float = 0.25


class ScoringResponse(BaseModel):
    method: Literal["WSM"] = "WSM"
    weights: ScoringWeights = Field(default_factory=ScoringWeights)


class DecisionResponse(BaseModel):
    items: list[RecommendedFoodResponse]
    total: int
    limit: int
    applied_filters: AppliedFilters
    scoring: ScoringResponse = Field(default_factory=ScoringResponse)


# Lưu giữ cho trường hợp cần dùng nội bộ / debug
class ExclusionReason(BaseModel):
    constraint: Literal[
        "budget_max",
        "meal_type",
        "max_prep_time",
        "excluded_ingredients",
        "invalid_data",
    ]
    message: str


class ExcludedFoodResponse(BaseModel):
    food_id: int
    name: str
    exclusion_reasons: list[ExclusionReason]
