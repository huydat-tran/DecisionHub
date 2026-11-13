"""Pydantic schemas cho module Travel.

Bao gồm:
  - TravelRecommendRequest: Yêu cầu gợi ý địa điểm du lịch.
  - TravelCriteriaScores: Điểm 3 tiêu chí WSM của Travel.
  - TravelAppliedFilters: Bộ lọc đã áp dụng (trả về trong response).
  - TravelRecommendedItem: Một địa điểm trong danh sách kết quả.
  - TravelScoringWeights: Trọng số 3 tiêu chí Travel.
  - TravelScoringResponse: Thông tin phương pháp chấm điểm.
  - TravelDecisionResponse: Response tổng hợp cho POST /recommend.
  - TravelPlaceDetail: Response cho GET /{place_id}.
  - TravelQuickSearchParams: Query params cho GET /quick-search.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------


class TravelRecommendRequest(BaseModel):
    """Body request cho POST /api/v1/travel/recommend.

    Rubric Travel (đã xác nhận):
      cost 0.40 | preference 0.35 | duration 0.25
    """

    budget_max: int = Field(
        ...,
        gt=0,
        description="Ngân sách tối đa (VND). Hard constraint bắt buộc.",
        examples=[1500000],
    )
    max_duration: float = Field(
        ...,
        gt=0,
        description="Thời lượng tối đa chấp nhận được (giờ). Hard constraint bắt buộc.",
        examples=[24.0],
    )
    regions: list[str] | None = Field(
        default=None,
        description=(
            "Danh sách khu vực ưu tiên (optional). "
            "Giá trị hợp lệ: Bắc, Trung, Nam, Tây Nguyên, Tây Nam Bộ."
        ),
        examples=[["Bắc", "Trung"]],
    )
    preferred_activity: str | None = Field(
        default=None,
        description=(
            "Loại hình trải nghiệm mong muốn (optional). "
            "Ví dụ: Khám phá thiên nhiên, Nghỉ dưỡng biển, Văn hóa lịch sử, "
            "Vui chơi giải trí, Sinh thái sông nước, Nghỉ dưỡng sinh thái."
        ),
        examples=["Khám phá thiên nhiên"],
    )
    top_n: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Số lượng địa điểm gợi ý tối đa. Mặc định 5, tối đa 20.",
    )


# ---------------------------------------------------------------------------
# Response components
# ---------------------------------------------------------------------------


class TravelCriteriaScores(BaseModel):
    """Điểm 3 tiêu chí WSM cho một địa điểm (thang 0–100)."""

    cost: float = Field(ge=0, le=100, description="Điểm tiêu chí Chi phí du lịch")
    preference: float = Field(ge=0, le=100, description="Điểm tiêu chí Mức phù hợp sở thích")
    duration: float = Field(ge=0, le=100, description="Điểm tiêu chí Thời lượng trải nghiệm")


class TravelAppliedFilters(BaseModel):
    """Bộ lọc đã áp dụng, trả về trong response để frontend hiển thị minh bạch."""

    budget_max: int
    max_duration: float
    regions: list[str] | None = None
    preferred_activity: str | None = None


class TravelRecommendedItem(BaseModel):
    """Một địa điểm du lịch trong danh sách kết quả gợi ý."""

    place_id: int
    name: str
    province_city: str
    region: str
    estimated_cost: int
    estimated_duration: float
    activity_type: str
    rating: float
    image_url: str | None = None
    score: float = Field(ge=0, le=100, description="Điểm WSM tổng hợp (0–100)")
    criteria_scores: TravelCriteriaScores
    reasons: list[str] = Field(
        default_factory=list,
        description="1–3 lý do giải thích dựa trên dữ liệu thực",
    )


class TravelScoringWeights(BaseModel):
    """Trọng số 3 tiêu chí Travel (tổng = 1.0)."""

    cost: float = 0.40
    preference: float = 0.35
    duration: float = 0.25


class TravelScoringResponse(BaseModel):
    """Thông tin phương pháp và trọng số chấm điểm."""

    method: str = "WSM"
    weights: TravelScoringWeights = Field(default_factory=TravelScoringWeights)


class TravelDecisionResponse(BaseModel):
    """Response tổng hợp cho POST /api/v1/travel/recommend."""

    items: list[TravelRecommendedItem]
    total: int = Field(description="Số địa điểm thực sự trả về")
    limit: int = Field(description="top_n đã yêu cầu")
    applied_filters: TravelAppliedFilters
    scoring: TravelScoringResponse = Field(default_factory=TravelScoringResponse)


# ---------------------------------------------------------------------------
# Quick Search & Detail
# ---------------------------------------------------------------------------


class TravelPlaceDetail(BaseModel):
    """Response cho GET /api/v1/travel/{place_id}."""

    place_id: int
    name: str
    province_city: str
    region: str
    estimated_cost: int
    estimated_duration: float
    activity_type: str
    highlights: list[str] = Field(default_factory=list)
    description: str | None = None
    image_url: str | None = None
    rating: float
    is_active: bool


class TravelQuickSearchItem(BaseModel):
    """Một địa điểm trong kết quả quick search."""

    place_id: int
    name: str
    province_city: str
    region: str
    estimated_cost: int
    estimated_duration: float
    activity_type: str
    image_url: str | None = None
    rating: float
