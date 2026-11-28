"""Pydantic schemas cho module Food (CRUD danh sách và chi tiết món ăn)."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

MealTypeLiteral = Literal["breakfast", "lunch", "dinner", "snack"]


def normalize_tags(raw_tags: Any) -> list[str]:
    """Chuẩn hóa cột JSON tags thành danh sách chuỗi sạch, không trùng lặp."""
    if raw_tags is None:
        return []
    if isinstance(raw_tags, str):
        items = [item.strip() for item in raw_tags.split(",") if item.strip()]
    elif isinstance(raw_tags, dict):
        items = [str(key).strip() for key, val in raw_tags.items() if val and str(key).strip()]
    elif isinstance(raw_tags, (list, tuple, set)):
        items = [str(item).strip() for item in raw_tags if item is not None and str(item).strip()]
    else:
        return []

    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def normalize_ingredients(raw_ingredients: Any) -> list[str]:
    """Chuẩn hóa danh sách nguyên liệu từ list[str], list[{name}] hoặc chuỗi phẩy."""
    if raw_ingredients is None:
        return []
    if isinstance(raw_ingredients, str):
        raw_items: list[Any] = raw_ingredients.split(",")
    elif isinstance(raw_ingredients, (list, tuple, set)):
        raw_items = list(raw_ingredients)
    else:
        raise ValueError("Danh sách nguyên liệu không hợp lệ.")

    seen: set[str] = set()
    result: list[str] = []
    for item in raw_items:
        if isinstance(item, dict):
            name = str(item.get("name", "")).strip()
        elif hasattr(item, "name"):
            name = str(item.name).strip()
        else:
            name = str(item).strip()

        if not name:
            continue
        if len(name) > 150:
            raise ValueError("Tên nguyên liệu không được vượt quá 150 ký tự.")
        key = name.lower()
        if key not in seen:
            seen.add(key)
            result.append(name)
    return result


def normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def validate_image_url(value: str | None) -> str | None:
    cleaned = normalize_optional_text(value)
    if cleaned is None:
        return None
    if not (cleaned.startswith("http://") or cleaned.startswith("https://")):
        raise ValueError("URL hình ảnh phải bắt đầu bằng http:// hoặc https://.")
    return cleaned


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


class FoodCreate(BaseModel):
    """Payload tạo mới món ăn từ trang Admin."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=255, description="Tên món ăn")
    price: int = Field(..., ge=0, description="Giá tham khảo (VND)")
    meal_type: MealTypeLiteral = Field(..., description="Loại bữa ăn")
    prep_time: int | None = Field(default=None, ge=0, description="Thời gian chuẩn bị (phút)")
    description: str | None = Field(default=None, max_length=1000, description="Mô tả món ăn")
    image_url: str | None = Field(default=None, max_length=500, description="URL hình ảnh")
    tags: list[str] = Field(default_factory=list, description="Danh sách nhãn")
    ingredients: list[str] = Field(default_factory=list, description="Danh sách nguyên liệu")
    is_active: bool = Field(default=True, description="Trạng thái hoạt động")

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Tên món ăn không được để trống.")
        return cleaned

    @field_validator("price", mode="before")
    @classmethod
    def coerce_price(cls, value: Any) -> Any:
        if isinstance(value, (Decimal, float)):
            return int(round(value))
        return value

    @field_validator("description", mode="before")
    @classmethod
    def clean_description(cls, value: str | None) -> str | None:
        return normalize_optional_text(value)

    @field_validator("image_url", mode="before")
    @classmethod
    def clean_image_url(cls, value: str | None) -> str | None:
        return validate_image_url(value)

    @field_validator("tags", mode="before")
    @classmethod
    def clean_tags(cls, value: Any) -> list[str]:
        return normalize_tags(value)

    @field_validator("ingredients", mode="before")
    @classmethod
    def clean_ingredients(cls, value: Any) -> list[str]:
        return normalize_ingredients(value)


class FoodUpdate(BaseModel):
    """Payload cập nhật món ăn từ trang Admin."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255, description="Tên món ăn")
    price: int | None = Field(default=None, ge=0, description="Giá tham khảo (VND)")
    meal_type: MealTypeLiteral | None = Field(default=None, description="Loại bữa ăn")
    prep_time: int | None = Field(default=None, ge=0, description="Thời gian chuẩn bị (phút)")
    description: str | None = Field(default=None, max_length=1000, description="Mô tả món ăn")
    image_url: str | None = Field(default=None, max_length=500, description="URL hình ảnh")
    tags: list[str] | None = Field(default=None, description="Danh sách nhãn")
    ingredients: list[str] | None = Field(default=None, description="Danh sách nguyên liệu")
    is_active: bool | None = Field(default=None, description="Trạng thái hoạt động")

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Tên món ăn không được để trống.")
        return cleaned

    @field_validator("price", mode="before")
    @classmethod
    def coerce_price(cls, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, (Decimal, float)):
            return int(round(value))
        return value

    @field_validator("description", mode="before")
    @classmethod
    def clean_description(cls, value: str | None) -> str | None:
        return normalize_optional_text(value)

    @field_validator("image_url", mode="before")
    @classmethod
    def clean_image_url(cls, value: str | None) -> str | None:
        return validate_image_url(value)

    @field_validator("tags", mode="before")
    @classmethod
    def clean_tags(cls, value: Any) -> list[str] | None:
        if value is None:
            return None
        return normalize_tags(value)

    @field_validator("ingredients", mode="before")
    @classmethod
    def clean_ingredients(cls, value: Any) -> list[str] | None:
        if value is None:
            return None
        return normalize_ingredients(value)


class FoodListResponse(BaseModel):
    """Response chuẩn cho API lấy danh sách món ăn."""

    success: bool = True
    message: str
    data: list[FoodOut]


class FoodDetailResponse(BaseModel):
    """Response chuẩn cho API chi tiết / tạo / cập nhật món ăn."""

    success: bool = True
    message: str
    data: FoodOut


class FoodDeletedData(BaseModel):
    """Dữ liệu xác nhận ID món ăn đã xoá."""

    id: int


class FoodDeleteResponse(BaseModel):
    """Response chuẩn cho API xoá món ăn."""

    success: bool = True
    message: str
    data: FoodDeletedData
