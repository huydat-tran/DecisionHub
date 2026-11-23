import math
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

VALID_MEAL_TYPES: tuple[str, ...] = ("breakfast", "lunch", "dinner", "snack")
WEIGHT_SUM_TOLERANCE: float = 1e-6

MealTypeLiteral = Literal["breakfast", "lunch", "dinner", "snack"]


class WeightsInput(BaseModel):
    """Trọng số WSM tùy chỉnh cho từng tiêu chí (0.0 - 1.0, tổng bằng 1.0)."""

    model_config = ConfigDict(extra="forbid")

    price: float = Field(..., description="Trọng số tiêu chí giá (0.0 - 1.0)")
    preference: float = Field(..., description="Trọng số tiêu chí khẩu vị/nhu cầu (0.0 - 1.0)")
    prep_time: float = Field(..., description="Trọng số tiêu chí thời gian chuẩn bị (0.0 - 1.0)")

    @field_validator("price", "preference", "prep_time", mode="before")
    @classmethod
    def validate_weight_value(cls, value: Any) -> float:
        """Kiểm tra từng trọng số là số thực hữu hạn nằm trong đoạn [0.0, 1.0]."""
        if isinstance(value, bool):
            raise ValueError("Trọng số phải là số thực hợp lệ (không được là boolean).")
        if value is None:
            raise ValueError("Trọng số không được để trống.")
        try:
            num = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("Trọng số phải là số thực hợp lệ.") from exc
        if not math.isfinite(num):
            raise ValueError(
                "Trọng số phải là số thực hữu hạn (không chấp nhận NaN hoặc Infinity)."
            )
        if num < 0:
            raise ValueError("Trọng số không được âm (phải >= 0).")
        if num > 1:
            raise ValueError("Trọng số không được vượt quá 1.0.")
        return num

    @model_validator(mode="after")
    def validate_weight_sum(self) -> "WeightsInput":
        """Kiểm tra tổng các trọng số bằng 1.0 trong sai số số thực."""
        total = self.price + self.preference + self.prep_time
        if not math.isclose(total, 1.0, abs_tol=WEIGHT_SUM_TOLERANCE):
            raise ValueError(f"Tổng trọng số phải bằng 1.0 (hiện tại: {total:.4f}).")
        return self


class DecisionRecommendRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    budget_max: int = Field(..., gt=0, description="Ngân sách tối đa (VNĐ)")
    meal_type: MealTypeLiteral | None = None
    max_prep_time: int | None = Field(default=None, gt=0, description="Phút")
    excluded_ingredients: list[str] = Field(default_factory=list)
    preferred_tags: list[str] = Field(default_factory=list)
    limit: int = Field(default=5, ge=1, le=20)
    weights: WeightsInput | None = Field(
        default=None,
        description="Trọng số WSM tùy chỉnh (tổng phải bằng 1.0; để trống dùng mặc định)",
    )

    @field_validator("budget_max", mode="before")
    @classmethod
    def validate_budget_max(cls, value: Any) -> int:
        """Kiểm tra ngân sách tối đa là số nguyên dương (> 0)."""
        if value is None:
            raise ValueError("Ngân sách tối đa (budget_max) không được để trống.")
        if isinstance(value, (bool, float)):
            raise ValueError(
                "Ngân sách tối đa (budget_max) phải là số nguyên dương lớn hơn 0."
            )
        if isinstance(value, str):
            stripped = value.strip()
            try:
                value = int(stripped)
            except ValueError as exc:
                raise ValueError(
                    "Ngân sách tối đa (budget_max) phải là số nguyên dương lớn hơn 0."
                ) from exc
        if not isinstance(value, int):
            raise ValueError(
                "Ngân sách tối đa (budget_max) phải là số nguyên dương lớn hơn 0."
            )
        if value <= 0:
            raise ValueError("Ngân sách tối đa (budget_max) phải lớn hơn 0.")
        return value

    @field_validator("meal_type", mode="before")
    @classmethod
    def validate_meal_type(cls, value: Any) -> str | None:
        """Kiểm tra loại bữa ăn hợp lệ hoặc None nếu không lọc theo bữa."""
        if value is None:
            return None
        if not isinstance(value, str) or value not in VALID_MEAL_TYPES:
            allowed = ", ".join(VALID_MEAL_TYPES)
            raise ValueError(
                f"Loại bữa ăn (meal_type) không hợp lệ. Chỉ chấp nhận: {allowed}."
            )
        return value

    @field_validator("excluded_ingredients", "preferred_tags",mode="before")
    @classmethod
    def clean_list(cls, value: Any) -> list[str]:
        # null -> [], bỏ rỗng/trùng, không phân biệt hoa thường
        if value is None:
            return []
        result: list[str] = []
        seen: set[str] = set()
        for raw in value:
            cleaned = str(raw).strip()
            key = cleaned.lower()
            if cleaned and key not in seen:
                seen.add(key)
                result.append(cleaned)
        return result

    @field_validator("limit", mode="before")
    @classmethod
    def default_limit(cls, value: Any) -> Any:
        return 5 if value is None else value


class DecisionHistoryItem(BaseModel):
    """Thông tin một bản ghi lịch sử quyết định của người dùng."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    domain: str
    input_snapshot: dict[str, Any]
    result_snapshot: dict[str, Any]
    created_at: datetime


class DecisionHistoryListResponse(BaseModel):
    """Response danh sách lịch sử quyết định của người dùng đang đăng nhập."""

    success: bool = True
    message: str = "Lấy danh sách lịch sử quyết định thành công."
    data: list[DecisionHistoryItem] = Field(default_factory=list)
    items: list[DecisionHistoryItem] = Field(default_factory=list)
    total: int = 0
    limit: int = 20
    offset: int = 0


class DecisionHistoryDetailResponse(BaseModel):
    """Response chi tiết một bản ghi lịch sử quyết định của người dùng."""

    success: bool = True
    message: str = "Lấy chi tiết lịch sử quyết định thành công."
    data: DecisionHistoryItem
    id: int
    user_id: int
    domain: str
    input_snapshot: dict[str, Any]
    result_snapshot: dict[str, Any]
    created_at: datetime
