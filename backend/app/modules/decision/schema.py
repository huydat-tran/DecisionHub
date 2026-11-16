from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

MealTypeLiteral = Literal["breakfast", "lunch", "dinner", "snack"]

class DecisionRecommendRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    budget_max: int = Field(..., gt= 0,description="Ngân sách tối đa (VNĐ)")
    meal_type: MealTypeLiteral | None = None
    max_prep_time: int | None = Field(default=None, gt = 0, description="Phút")
    excluded_ingredients: list[str] = Field(default_factory=list)
    preferred_tags: list[str] = Field(default_factory=list)
    limit:int = Field(default=5,ge=1,le=20)

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