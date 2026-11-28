"""Pydantic schemas cho module Travel (CRUD quản trị & Recommendation)."""

from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from enum import Enum
import math
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.travel.models import TravelRegion

_HTTP_URL_RE = re.compile(r"^https?://\S+$", re.IGNORECASE)


def _strip_required_text(value: Any, *, field_label: str, max_length: int) -> str:
    """Chuẩn hóa chuỗi bắt buộc: cắt khoảng trắng đầu/cuối, cấm rỗng và kiểm tra độ dài."""
    if not isinstance(value, str):
        raise ValueError(f"{field_label} phải là chuỗi ký tự.")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_label} không được để trống.")
    if len(cleaned) > max_length:
        raise ValueError(f"{field_label} không được vượt quá {max_length} ký tự.")
    return cleaned


def _strip_optional_text(value: Any, *, field_label: str, max_length: int | None = None) -> str | None:
    """Chuẩn hóa chuỗi tùy chọn: rỗng/whitespace thành None, kiểm tra độ dài nếu có."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_label} phải là chuỗi ký tự.")
    cleaned = value.strip()
    if not cleaned:
        return None
    if max_length is not None and len(cleaned) > max_length:
        raise ValueError(f"{field_label} không được vượt quá {max_length} ký tự.")
    return cleaned


def _validate_image_url(value: Any) -> str | None:
    """Kiểm tra URL hình ảnh tùy chọn: hỗ trợ rỗng -> None, tối đa 500 ký tự, http/https."""
    cleaned = _strip_optional_text(value, field_label="URL hình ảnh", max_length=500)
    if cleaned is None:
        return None
    if not _HTTP_URL_RE.match(cleaned):
        raise ValueError("URL hình ảnh phải bắt đầu bằng http:// hoặc https:// và không chứa khoảng trắng.")
    return cleaned


def _reject_bool_int(value: Any, *, field_label: str) -> Any:
    """Từ chối kiểu bool khi Pydantic parse số nguyên."""
    if isinstance(value, bool):
        raise ValueError(f"{field_label} phải là số nguyên hợp lệ.")
    return value


def _parse_decimal_number(
    value: Any,
    *,
    field_label: str,
    scale: str = "0.1",
) -> Decimal:
    """Chuyển đổi giá trị số sang Decimal hữu hạn với độ chính xác 1 chữ số thập phân."""
    if isinstance(value, bool):
        raise ValueError(f"{field_label} phải là số hợp lệ.")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{field_label} phải là số hữu hạn.")
    try:
        dec = value if isinstance(value, Decimal) else Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        raise ValueError(f"{field_label} phải là số hợp lệ.") from None
    if not dec.is_finite():
        raise ValueError(f"{field_label} phải là số hữu hạn.")
    return dec.quantize(Decimal(scale), rounding=ROUND_HALF_UP)


def normalize_highlights_input(value: Any) -> list[str]:
    """Chuẩn hóa danh sách hoạt động nổi bật từ list hoặc chuỗi phân tách dấu phẩy/dòng."""
    if value is None:
        return []
    if isinstance(value, str):
        raw_items = [value]
    elif isinstance(value, (list, tuple)):
        for item in value:
            if not isinstance(item, str):
                raise ValueError("Mỗi hoạt động nổi bật phải là chuỗi ký tự.")
        raw_items = list(value)
    else:
        raise ValueError("Danh sách hoạt động nổi bật phải là danh sách chuỗi hoặc chuỗi văn bản.")

    result: list[str] = []
    seen: set[str] = set()
    for raw in raw_items:
        for part in raw.replace("\n", ",").split(","):
            cleaned = part.strip()
            key = cleaned.lower()
            if cleaned and key not in seen:
                seen.add(key)
                result.append(cleaned)
    return result


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


_NON_NULLABLE_UPDATE_FIELDS: tuple[str, ...] = (
    "name",
    "province_city",
    "region",
    "estimated_cost",
    "estimated_duration",
    "activity_type",
    "rating",
    "is_active",
)


class TravelPlaceCreateRequest(BaseModel):
    """Payload tạo mới địa điểm du lịch (Admin)."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="Tên địa điểm du lịch (duy nhất, tối đa 200 ký tự)")
    province_city: str = Field(description="Tỉnh hoặc thành phố trực thuộc (tối đa 100 ký tự)")
    region: TravelRegion = Field(description="Khu vực địa lý (Bắc, Trung, Nam, Tây Nguyên, Tây Nam Bộ)")
    estimated_cost: int = Field(default=0, ge=0, description="Chi phí tham khảo trung bình (VND)")
    estimated_duration: Decimal = Field(
        default=Decimal("1.0"),
        gt=Decimal("0"),
        le=Decimal("999.9"),
        description="Thời lượng trải nghiệm ước tính (giờ, > 0 và <= 999.9)",
    )
    activity_type: str = Field(description="Loại hình trải nghiệm chính (tối đa 100 ký tự)")
    highlights: list[str] = Field(
        default_factory=list,
        description="Danh sách hoạt động nổi bật (list chuỗi hoặc chuỗi phân tách dấu phẩy/dòng)",
    )
    description: str | None = Field(default=None, description="Mô tả chi tiết về địa điểm")
    image_url: str | None = Field(default=None, description="URL hình ảnh minh họa (http/https)")
    rating: Decimal = Field(
        default=Decimal("4.5"),
        ge=Decimal("1.0"),
        le=Decimal("5.0"),
        description="Điểm đánh giá tham khảo (1.0 - 5.0)",
    )
    is_active: bool = Field(default=True, description="Trạng thái hoạt động")

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value: Any) -> str:
        return _strip_required_text(value, field_label="Tên địa điểm", max_length=200)

    @field_validator("province_city", mode="before")
    @classmethod
    def validate_province_city(cls, value: Any) -> str:
        return _strip_required_text(value, field_label="Tỉnh/Thành phố", max_length=100)

    @field_validator("activity_type", mode="before")
    @classmethod
    def validate_activity_type(cls, value: Any) -> str:
        return _strip_required_text(value, field_label="Loại hình trải nghiệm", max_length=100)

    @field_validator("estimated_cost", mode="before")
    @classmethod
    def validate_estimated_cost(cls, value: Any) -> Any:
        return _reject_bool_int(value, field_label="Chi phí tham khảo")

    @field_validator("estimated_duration", mode="before")
    @classmethod
    def validate_estimated_duration(cls, value: Any) -> Decimal:
        return _parse_decimal_number(value, field_label="Thời lượng ước tính")

    @field_validator("rating", mode="before")
    @classmethod
    def validate_rating(cls, value: Any) -> Decimal:
        return _parse_decimal_number(value, field_label="Điểm đánh giá")

    @field_validator("highlights", mode="before")
    @classmethod
    def validate_highlights(cls, value: Any) -> list[str]:
        return normalize_highlights_input(value)

    @field_validator("description", mode="before")
    @classmethod
    def validate_description(cls, value: Any) -> str | None:
        return _strip_optional_text(value, field_label="Mô tả")

    @field_validator("image_url", mode="before")
    @classmethod
    def validate_image_url(cls, value: Any) -> str | None:
        return _validate_image_url(value)


class TravelPlaceUpdateRequest(BaseModel):
    """Payload cập nhật một phần địa điểm du lịch (PATCH, Admin)."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, description="Tên địa điểm du lịch (duy nhất, tối đa 200 ký tự)")
    province_city: str | None = Field(default=None, description="Tỉnh hoặc thành phố trực thuộc")
    region: TravelRegion | None = Field(default=None, description="Khu vực địa lý")
    estimated_cost: int | None = Field(default=None, ge=0, description="Chi phí tham khảo trung bình (VND)")
    estimated_duration: Decimal | None = Field(
        default=None,
        gt=Decimal("0"),
        le=Decimal("999.9"),
        description="Thời lượng trải nghiệm ước tính (giờ)",
    )
    activity_type: str | None = Field(default=None, description="Loại hình trải nghiệm chính")
    highlights: list[str] | None = Field(
        default=None,
        description="Danh sách hoạt động nổi bật (truyền null hoặc [] để xóa)",
    )
    description: str | None = Field(default=None, description="Mô tả chi tiết về địa điểm")
    image_url: str | None = Field(default=None, description="URL hình ảnh minh họa (http/https)")
    rating: Decimal | None = Field(
        default=None,
        ge=Decimal("1.0"),
        le=Decimal("5.0"),
        description="Điểm đánh giá tham khảo (1.0 - 5.0)",
    )
    is_active: bool | None = Field(default=None, description="Trạng thái hoạt động")

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value: Any) -> str | None:
        if value is None:
            return None
        return _strip_required_text(value, field_label="Tên địa điểm", max_length=200)

    @field_validator("province_city", mode="before")
    @classmethod
    def validate_province_city(cls, value: Any) -> str | None:
        if value is None:
            return None
        return _strip_required_text(value, field_label="Tỉnh/Thành phố", max_length=100)

    @field_validator("activity_type", mode="before")
    @classmethod
    def validate_activity_type(cls, value: Any) -> str | None:
        if value is None:
            return None
        return _strip_required_text(value, field_label="Loại hình trải nghiệm", max_length=100)

    @field_validator("estimated_cost", mode="before")
    @classmethod
    def validate_estimated_cost(cls, value: Any) -> Any:
        if value is None:
            return None
        return _reject_bool_int(value, field_label="Chi phí tham khảo")

    @field_validator("estimated_duration", mode="before")
    @classmethod
    def validate_estimated_duration(cls, value: Any) -> Decimal | None:
        if value is None:
            return None
        return _parse_decimal_number(value, field_label="Thời lượng ước tính")

    @field_validator("rating", mode="before")
    @classmethod
    def validate_rating(cls, value: Any) -> Decimal | None:
        if value is None:
            return None
        return _parse_decimal_number(value, field_label="Điểm đánh giá")

    @field_validator("highlights", mode="before")
    @classmethod
    def validate_highlights(cls, value: Any) -> list[str] | None:
        if value is None:
            return None
        return normalize_highlights_input(value)

    @field_validator("description", mode="before")
    @classmethod
    def validate_description(cls, value: Any) -> str | None:
        return _strip_optional_text(value, field_label="Mô tả")

    @field_validator("image_url", mode="before")
    @classmethod
    def validate_image_url(cls, value: Any) -> str | None:
        return _validate_image_url(value)

    @model_validator(mode="after")
    def reject_explicit_null_for_required_fields(self) -> "TravelPlaceUpdateRequest":
        for field_name in _NON_NULLABLE_UPDATE_FIELDS:
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"Trường '{field_name}' không được phép nhận giá trị null.")
        return self


class TravelPlaceOut(BaseModel):
    """Thông tin chuẩn hóa của một địa điểm du lịch trả về cho client."""

    model_config = ConfigDict(from_attributes=True)

    id: int
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
    created_at: datetime
    updated_at: datetime

    @field_validator("region", mode="before")
    @classmethod
    def coerce_region(cls, value: Any) -> str:
        if isinstance(value, Enum):
            return str(value.value)
        return str(value)

    @field_validator("highlights", mode="before")
    @classmethod
    def coerce_highlights(cls, value: Any) -> list[str]:
        return normalize_highlights_input(value)

    @field_validator("estimated_duration", "rating", mode="before")
    @classmethod
    def coerce_decimal_to_float(cls, value: Any) -> float:
        return float(value)


class TravelPlaceDetailResponse(BaseModel):
    """Response chuẩn cho API chi tiết / tạo / cập nhật địa điểm du lịch."""

    success: bool = True
    message: str
    data: TravelPlaceOut


class TravelPlaceListData(BaseModel):
    """Dữ liệu phân trang danh sách địa điểm du lịch."""

    items: list[TravelPlaceOut] = Field(default_factory=list)
    total: int = 0
    limit: int = 20
    offset: int = 0


class TravelPlaceListResponse(BaseModel):
    """Response chuẩn cho API lấy danh sách địa điểm du lịch."""

    success: bool = True
    message: str
    data: TravelPlaceListData


class TravelPlaceDeleteData(BaseModel):
    """Thông tin địa điểm đã xóa."""

    id: int
    name: str


class TravelPlaceDeleteResponse(BaseModel):
    """Response chuẩn cho API xóa địa điểm du lịch."""

    success: bool = True
    message: str
    data: TravelPlaceDeleteData
