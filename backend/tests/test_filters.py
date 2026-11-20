"""Unit tests cho Bước 2 - Lọc điều kiện bắt buộc (Hard Constraints)."""

from decimal import Decimal
from enum import Enum
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

# Đảm bảo import được `app.*` khi chạy từ root repo hoặc từ `backend/`
"""Unit tests cho Hard Constraint Filtering và tích hợp vào Decision Engine Pipeline.

Kiểm tra: filters.py (lọc ứng viên) → pipeline.py (thứ tự lọc trước chấm điểm).
"""

from decimal import Decimal
from pathlib import Path
import sys
import unittest

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
from app.modules.decision.engine.pipeline import evaluate

CRITERIA = [
    {"domain": "food", "name": "Giá", "direction": "min", "weight": Decimal("0.5000")},
    {
        "domain": "food",
        "name": "Mức phù hợp nhu cầu/khẩu vị",
        "direction": "max",
        "weight": Decimal("0.5000"),
    },
]


def _food(
    food_id: int,
    name: str,
    price: int,
    meal_type: str = "lunch",
    prep_time: int | None = 15,
    ingredients: list[str] | None = None,
) -> dict:
    return {
        "id": food_id,
        "name": name,
        "price": price,
        "meal_type": meal_type,
        "prep_time": prep_time,
        "ingredients": ingredients if ingredients is not None else [],
        "preference": 80,
    }


class TestFilterCandidates(unittest.TestCase):
    def test_candidate_passing_all_constraints_is_kept(self) -> None:
        candidates = [_food(1, "Món A", 30_000, ingredients=["thịt bò"])]
        kept = filter_candidates(
            candidates,
            budget_max=50_000,
            meal_type="lunch",
            max_prep_time=30,
            excluded_ingredients=["hành"],
        )
        self.assertEqual([c["id"] for c in kept], [1])

    def test_candidate_over_budget_is_removed(self) -> None:
        candidates = [_food(1, "Món A", 60_000)]
        kept = filter_candidates(candidates, budget_max=50_000)
        self.assertEqual(kept, [])

    def test_candidate_with_wrong_meal_type_is_removed(self) -> None:
        candidates = [_food(1, "Món A", 30_000, meal_type="dinner")]
        kept = filter_candidates(candidates, meal_type="lunch")
        self.assertEqual(kept, [])

    def test_candidate_with_excluded_ingredient_is_removed(self) -> None:
        candidates = [_food(1, "Món A", 30_000, ingredients=["Tôm chua"])]
        kept = filter_candidates(candidates, excluded_ingredients=["tôm"])
        self.assertEqual(kept, [])

    def test_candidate_with_prep_time_over_limit_is_removed(self) -> None:
        candidates = [_food(1, "Món A", 30_000, prep_time=45)]
        kept = filter_candidates(candidates, max_prep_time=30)
        self.assertEqual(kept, [])

    def test_candidate_with_prep_time_equal_limit_is_kept(self) -> None:
        candidates = [_food(1, "Món A", 30_000, prep_time=30)]
        kept = filter_candidates(candidates, max_prep_time=30)
        self.assertEqual([c["id"] for c in kept], [1])

    def test_max_prep_time_not_provided_does_not_filter(self) -> None:
        candidates = [_food(1, "Món A", 30_000, prep_time=999)]
        kept = filter_candidates(candidates)
        self.assertEqual([c["id"] for c in kept], [1])

    def test_missing_prep_time_is_removed_when_limit_provided(self) -> None:
        candidates = [_food(1, "Món A", 30_000, prep_time=None)]
        kept = filter_candidates(candidates, max_prep_time=30)
        self.assertEqual(kept, [])

    def test_invalid_prep_time_type_is_removed_without_error(self) -> None:
        candidates = [_food(1, "Món A", 30_000, prep_time="nhanh")]
        kept = filter_candidates(candidates, max_prep_time=30)
        self.assertEqual(kept, [])

    def test_negative_max_prep_time_raises(self) -> None:
        with self.assertRaises(ValueError):
            filter_candidates([_food(1, "Món A", 30_000)], max_prep_time=-1)

    def test_passes_hard_constraints_handles_missing_price(self) -> None:
        candidate = {"id": 1, "name": "Món A"}
        self.assertFalse(passes_hard_constraints(candidate, budget_max=50_000))


class TestPipelineIntegratesFiltering(unittest.TestCase):
    def test_filtering_runs_before_scoring(self) -> None:
        """Ứng viên vi phạm ràng buộc không được đưa vào Scoring (điểm không tính lại)."""
        candidates = [
            _food(1, "Món A", 30_000, prep_time=10),
            _food(2, "Món B", 30_000, prep_time=60),
        ]
        results = evaluate(candidates, CRITERIA, domain="food", max_prep_time=30)

        self.assertEqual([r["id"] for r in results], [1])
        # Min-Max chỉ được tính trên tập còn lại: 1 ứng viên → min == max → 100 điểm
        self.assertEqual(results[0]["criteria_scores"]["price"], 100.0)

    def test_all_candidates_removed_returns_empty_list(self) -> None:
        candidates = [_food(1, "Món A", 90_000)]
        results = evaluate(candidates, CRITERIA, domain="food", budget_max=50_000)
        self.assertEqual(results, [])

    def test_empty_candidates_returns_empty_list(self) -> None:
        self.assertEqual(evaluate([], CRITERIA, domain="food"), [])

    def test_evaluate_without_constraints_keeps_all_candidates(self) -> None:
        candidates = [_food(1, "Món A", 90_000, prep_time=999)]
        results = evaluate(candidates, CRITERIA, domain="food")
        self.assertEqual([r["id"] for r in results], [1])

    def test_engine_does_not_import_database(self) -> None:
        """Engine không được phụ thuộc SQLAlchemy/session (không truy vấn DB bên trong)."""
        source = (BACKEND_DIR / "app" / "modules" / "decision" / "engine" / "pipeline.py").read_text(
            encoding="utf-8"
        )
        for forbidden in ("sqlalchemy", "Session", "get_db"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
