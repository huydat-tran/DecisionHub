from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class CriteriaScores(BaseModel):
    price: float
    preference: float
    prep_time: float


class CriterionDetail(BaseModel):
    """Thông tin chi tiết của một tiêu chí đánh giá theo công thức WSM."""

    normalized_score: float | None = None
    weight: float
    contribution: float = 0.0


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
    total_score: float = Field(ge=0, le=100)
    rank: int = Field(default=1, ge=1)
    criteria_scores: CriteriaScores
    criteria_details: dict[str, CriterionDetail] = Field(default_factory=dict)
    reasons: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def set_defaults(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "total_score" not in data and "score" in data:
                data["total_score"] = data["score"]
            if "rank" not in data:
                data["rank"] = 1
        return data


class ScoringWeights(BaseModel):
    price: float = 0.40
    preference: float = 0.35
    prep_time: float = 0.25


class ScoringResponse(BaseModel):
    method: Literal["WSM"] = "WSM"
    weights: ScoringWeights = Field(default_factory=ScoringWeights)


class ExcludedOptionResponse(BaseModel):
    """Thống kê phương án bị loại qua các điều kiện bắt buộc."""

    id: int | str
    name: str
    status: Literal["excluded"] = "excluded"
    is_excluded: bool = True
    exclusion_reason: str
    exclusion_reasons: list[str] = Field(default_factory=list)


class DecisionResponse(BaseModel):
    """Response trả về kết quả gợi ý theo WSM và thống kê phương án bị loại."""

    success: bool = True
    message: str = "Đánh giá thành công."
    has_valid_candidates: bool = True
    items: list[RecommendedFoodResponse] = Field(default_factory=list)
    excluded_items: list[ExcludedOptionResponse] = Field(default_factory=list)
    total: int = 0
    total_excluded: int = 0
    limit: int = 5
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
