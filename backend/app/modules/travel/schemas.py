"""Pydantic schemas cho module Travel Recommendation."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.travel.models import TravelRegion


def normalize_str_list(values: list[str] | None) -> list[str]:
    """Tách chuỗi phân tách dấu phẩy, loại bỏ rỗng và trùng lặp không phân biệt hoa thường."""
    if not values:
        return []
    result: list[str] = []
    seen: set[str] = set()
    for raw in values:
        for part in str(raw).split(","):
            cleaned = part.strip()
            key = cleaned.lower()
            if cleaned and key not in seen:
                seen.add(key)
                result.append(cleaned)
    return result


class TravelRecommendRequest(BaseModel):
    """Dữ liệu client gửi lên để gợi ý địa điểm du lịch theo tiêu chí (WSM)."""

    model_config = ConfigDict(extra="forbid")

    budget_max: int | None = Field(
        default=None,
        ge=0,
        description="Ngân sách tối đa (VND)",
    )
    max_duration: float | None = Field(
        default=None,
        ge=0,
        description="Thời lượng tối đa (giờ)",
    )
    region: TravelRegion | None = Field(
        default=None,
        description="Khu vực địa lý (Bắc, Trung, Nam, Tây Nguyên, Tây Nam Bộ)",
    )
    activity_type: str | None = Field(
        default=None,
        description="Loại hình trải nghiệm chính",
    )
    preferred_activities: list[str] = Field(
        default_factory=list,
        description="Danh sách hoạt động hoặc sở thích ưu tiên",
    )
    limit: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Số lượng địa điểm gợi ý tối đa (1-20)",
    )

    @field_validator("preferred_activities", mode="before")
    @classmethod
    def clean_preferred_activities(cls, value: list[str] | None) -> list[str]:
        return normalize_str_list(value)


class RecommendedTravelResponse(BaseModel):
    """Thông tin một địa điểm du lịch được đề xuất kèm điểm WSM và lý do."""

    destination_id: int
    name: str
    province_city: str
    region: str
    estimated_cost: int
    estimated_duration: float
    activity_type: str
    highlights: list[str] = Field(default_factory=list)
    description: str | None = None
    image_url: str | None = None
    rating: float | None = None
    score: float = Field(ge=0, le=100)
    total_score: float = Field(ge=0, le=100)
    rank: int = Field(default=1, ge=1)
    criteria_scores: dict[str, float | None] = Field(default_factory=dict)
    criteria_details: dict[str, Any] = Field(default_factory=dict)
    reasons: list[str] = Field(default_factory=list)
    id: int | None = None


class TravelAppliedFilters(BaseModel):
    """Thông tin các bộ lọc đã áp dụng trong yêu cầu gợi ý."""

    budget_max: int | None = None
    max_duration: float | None = None
    region: str | None = None
    activity_type: str | None = None
    preferred_activities: list[str] = Field(default_factory=list)


class TravelScoringResponse(BaseModel):
    """Thông tin phương pháp tính điểm và trọng số tiêu chí."""

    method: str = "WSM"
    weights: dict[str, float] = Field(default_factory=dict)


class TravelExcludedOptionResponse(BaseModel):
    """Thông tin phương án bị loại bởi điều kiện bắt buộc."""

    id: int | str | None = None
    name: str
    status: str = "excluded"
    is_excluded: bool = True
    exclusion_reason: str
    exclusion_reasons: list[str] = Field(default_factory=list)


class TravelDecisionData(BaseModel):
    """Dữ liệu kết quả gợi ý địa điểm du lịch."""

    items: list[RecommendedTravelResponse] = Field(default_factory=list)
    excluded_items: list[TravelExcludedOptionResponse] = Field(default_factory=list)
    total: int = 0
    total_excluded: int = 0
    limit: int = 5
    applied_filters: TravelAppliedFilters
    scoring: TravelScoringResponse


class TravelRecommendResponse(BaseModel):
    """Response chuẩn cho API gợi ý địa điểm du lịch theo tiêu chí."""

    success: bool = True
    message: str
    data: TravelDecisionData
