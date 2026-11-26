"""Pydantic schemas cho module Food (Danh sách và Chi tiết món ăn)."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


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


class FoodListResponse(BaseModel):
    """Response chuẩn cho API lấy danh sách tất cả món ăn."""

    success: bool = True
    message: str
    data: list[FoodOut]


class FoodDetailResponse(BaseModel):
    """Response chuẩn cho API chi tiết món ăn."""

    success: bool = True
    message: str
    data: FoodOut
