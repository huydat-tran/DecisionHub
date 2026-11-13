"""Pydantic schemas cho module Food (Quick Search, Chi tiết món ăn, Recommendation)."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.decision.decision_response import DecisionResponse


class MealType(str, Enum):
    """Loại bữa ăn được hỗ trợ trong hệ thống."""

    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class FoodSortBy(str, Enum):
    """Tiêu chí sắp xếp cho Quick Search."""

    RELEVANCE = "relevance"
    PRICE_ASC = "price_asc"
    PREP_TIME_ASC = "prep_time_asc"


def normalize_tags(raw_tags: Any) -> list[str]:
    """Chuẩn hóa cột JSON tags thành danh sách chuỗi sạch."""
    if raw_tags is None:
        return []
    if isinstance(raw_tags, str):
        return [item.strip() for item in raw_tags.split(",") if item.strip()]
    if isinstance(raw_tags, dict):
        return [str(key).strip() for key, val in raw_tags.items() if val and str(key).strip()]
    if isinstance(raw_tags, (list, tuple, set)):
        return [str(item).strip() for item in raw_tags if item is not None and str(item).strip()]
    return []


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


class IngredientOut(BaseModel):
    """Thông tin nguyên liệu của món ăn trả về cho client."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class FoodOut(BaseModel):
    """Thông tin món ăn chuẩn hóa trả về từ server."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    price: int = Field(ge=0, description="Giá tham khảo (VND)")
    meal_type: str
    prep_time: int | None = Field(default=None, ge=0, description="Thời gian chuẩn bị (phút)")
    image_url: str | None = None
    tags: list[str] = Field(default_factory=list)
    ingredients: list[IngredientOut] = Field(default_factory=list)
    is_active: bool
    created_at: datetime

    @field_validator("price", mode="before")
    @classmethod
    def coerce_price_to_int(cls, value: int | float | Decimal) -> int:
        if isinstance(value, (Decimal, float)):
            return int(round(value))
        return value

    @field_validator("tags", mode="before")
    @classmethod
    def coerce_tags(cls, value: Any) -> list[str]:
        return normalize_tags(value)


class FoodQuickSearchFilters(BaseModel):
    """Bộ lọc tìm kiếm nhanh đã được chuẩn hóa."""

    q: str | None = Field(
        default=None,
        max_length=100,
        description="Từ khóa tìm theo tên, mô tả, nhãn hoặc nguyên liệu",
    )
    meal_type: MealType | None = Field(default=None, description="Loại bữa ăn")
    max_price: int | None = Field(default=None, ge=0, description="Giá tối đa (VND)")
    max_prep_time: int | None = Field(
        default=None,
        ge=0,
        description="Thời gian chuẩn bị tối đa (phút)",
    )
    excluded_ingredients: list[str] = Field(
        default_factory=list,
        description="Nguyên liệu cần tránh",
    )
    tags: list[str] = Field(default_factory=list, description="Nhãn cần có")
    sort_by: FoodSortBy = Field(default=FoodSortBy.RELEVANCE, description="Cách sắp xếp")

    @field_validator("q")
    @classmethod
    def strip_keyword(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("excluded_ingredients", "tags", mode="before")
    @classmethod
    def clean_list_fields(cls, value: list[str] | None) -> list[str]:
        return normalize_str_list(value)


class FoodQuickSearchData(BaseModel):
    """Payload kết quả tìm kiếm nhanh món ăn."""

    items: list[FoodOut]
    total: int
    limit: int
    offset: int
    filters_applied: FoodQuickSearchFilters


class FoodQuickSearchResponse(BaseModel):
    """Response chuẩn cho API Quick Search món ăn."""

    success: bool = True
    message: str
    data: FoodQuickSearchData


class FoodDetailResponse(BaseModel):
    """Response chuẩn cho API chi tiết món ăn."""

    success: bool = True
    message: str
    data: FoodOut


class FoodRecommendRequest(BaseModel):
    """Dữ liệu client gửi lên để gợi ý món ăn theo tiêu chí (WSM)."""

    model_config = ConfigDict(extra="forbid")

    budget_max: int = Field(..., ge=0, description="Ngân sách tối đa (VND)")
    meal_type: MealType | None = Field(
        default=None,
        description="Loại bữa ăn bắt buộc (nếu chọn)",
    )
    max_prep_time: int | None = Field(
        default=None,
        ge=0,
        description="Thời gian chuẩn bị tối đa (phút)",
    )
    excluded_ingredients: list[str] = Field(
        default_factory=list,
        description="Danh sách nguyên liệu cần tránh",
    )
    preferred_tags: list[str] = Field(
        default_factory=list,
        description="Danh sách nhãn/khẩu vị ưu tiên",
    )
    limit: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Số lượng món gợi ý tối đa (1-20)",
    )

    @field_validator("excluded_ingredients", "preferred_tags", mode="before")
    @classmethod
    def clean_list_fields(cls, value: list[str] | None) -> list[str]:
        return normalize_str_list(value)


class FoodRecommendResponse(BaseModel):
    """Response chuẩn cho API gợi ý món ăn theo tiêu chí."""

    success: bool = True
    message: str
    data: DecisionResponse
