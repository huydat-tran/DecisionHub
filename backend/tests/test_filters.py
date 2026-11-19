"""Unit tests cho Bước 2 - Lọc điều kiện bắt buộc (Hard Constraints)."""

from decimal import Decimal
from enum import Enum
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

# Đảm bảo import được `app.*` khi chạy từ root repo hoặc từ `backend/`
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.modules.decision.engine.filters import filter_candidates, passes_hard_constraints


class MealTypeEnum(Enum):
    SANG = "sang"
    TRUA = "trua"
    TOI = "toi"


class TestHardConstraintBudget(unittest.TestCase):
    def test_budget_max_filters_exceeding_and_keeps_boundary(self) -> None:
        candidates = [
            {"id": 1, "name": "Bánh mì", "price": 25_000},
            {"id": 2, "name": "Phở bò", "price": Decimal("50000")},
            {"id": 3, "name": "Lẩu", "price": 120_000},
        ]
        result = filter_candidates(candidates, budget_max=50_000)
        self.assertEqual([item["id"] for item in result], [1, 2])

    def test_budget_max_excludes_missing_negative_and_invalid_prices(self) -> None:
        candidates = [
            {"id": 1, "name": "Thiếu giá", "price": None},
            {"id": 2, "name": "Giá âm", "price": -10_000},
            {"id": 3, "name": "Bool", "price": True},
            {"id": 4, "name": "NaN", "price": float("nan")},
            {"id": 5, "name": "Inf", "price": float("inf")},
            {"id": 6, "name": "Chuỗi rỗng", "price": ""},
            {"id": 7, "name": "Không phải số", "price": "abc"},
            {"id": 8, "name": "Hợp lệ", "price": "35000"},
        ]
        result = filter_candidates(candidates, budget_max=40_000)
        self.assertEqual([item["id"] for item in result], [8])

    def test_invalid_budget_max_raises_value_error(self) -> None:
        for invalid in (-1, -0.01, float("nan"), float("inf"), True, "abc"):
            with self.subTest(budget_max=invalid):
                with self.assertRaises(ValueError):
                    filter_candidates([{"id": 1, "price": 10_000}], budget_max=invalid)
                with self.assertRaises(ValueError):
                    passes_hard_constraints({"id": 1, "price": 10_000}, budget_max=invalid)


class TestHardConstraintMealType(unittest.TestCase):
    def test_meal_type_matches_case_insensitive_and_enum(self) -> None:
        candidates = [
            {"id": 1, "meal_type": "  Sang  "},
            {"id": 2, "meal_type": MealTypeEnum.TRUA},
            {"id": 3, "meal_type": "toi"},
            {"id": 4, "meal_type": None},
            {"id": 5, "meal_type": ""},
        ]
        self.assertEqual(
            [c["id"] for c in filter_candidates(candidates, meal_type="SANG")],
            [1],
        )
        self.assertEqual(
            [c["id"] for c in filter_candidates(candidates, meal_type=MealTypeEnum.TRUA)],
            [2],
        )


class TestHardConstraintExcludedIngredients(unittest.TestCase):
    def test_excluded_ingredients_supports_str_dict_and_object(self) -> None:
        candidates = [
            {"id": 1, "ingredients": ["Thịt bò", "Hành lá"]},
            {"id": 2, "ingredients": [{"name": "Mắm tôm"}, {"name": "Bún"}]},
            SimpleNamespace(id=3, ingredients=[SimpleNamespace(name="Đậu phộng")]),
            {"id": 4, "ingredients": ["Gà", "Gừng"]},
            {"id": 5, "ingredients": "Tôm sú"},
            {"id": 6, "ingredients": []},
        ]
        result = filter_candidates(
            candidates,
            excluded_ingredients=["  tôm ", "ĐẬU PHỘNG", ""],
        )
        result_ids = [item["id"] if isinstance(item, dict) else item.id for item in result]
        self.assertEqual(result_ids, [1, 4, 6])


class TestHardConstraintsCombined(unittest.TestCase):
    def test_no_compensation_when_any_constraint_fails(self) -> None:
        candidates = [
            {"id": 1, "price": 30_000, "meal_type": "trua", "ingredients": ["Thịt heo"]},
            {"id": 2, "price": 20_000, "meal_type": "sang", "ingredients": ["Thịt heo"]},
            {"id": 3, "price": 20_000, "meal_type": "trua", "ingredients": ["Hành"]},
            {"id": 4, "price": 60_000, "meal_type": "trua", "ingredients": ["Thịt heo"]},
        ]
        result = filter_candidates(
            candidates,
            budget_max=40_000,
            meal_type="trua",
            excluded_ingredients=["hành"],
        )
        self.assertEqual([item["id"] for item in result], [1])

    def test_all_candidates_filtered_returns_empty_list(self) -> None:
        candidates = [
            {"id": 1, "price": 80_000, "meal_type": "trua", "ingredients": []},
        ]
        self.assertEqual(filter_candidates(candidates, budget_max=50_000), [])

    def test_no_constraints_keeps_all_candidates(self) -> None:
        candidates = [{"id": 1}, {"id": 2, "price": None}]
        self.assertEqual(filter_candidates(candidates), candidates)


if __name__ == "__main__":
    unittest.main()
