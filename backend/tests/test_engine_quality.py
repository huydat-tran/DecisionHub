"""Test hồi quy cho các vấn đề P1/P2 của Decision Engine.

Kiểm tra:
1. excluded_candidates được giới hạn nhưng total_excluded không bị mất.
2. _explain_constraint không còn dead code, thông báo Hard Constraint Food chính xác.
3. Enum hiển thị đúng giá trị (không phải MealType.dinner).
4. Các hàm public import được từ app.modules.decision.engine.
5. _extract_candidate_id không trả về ID giả bằng 0.
"""

from decimal import Decimal
from enum import Enum
from pathlib import Path
import sys
import unittest

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.modules.decision.engine import (
    evaluate_decision,
    filter_and_explain_candidates,
    inspect_candidate,
)
from app.modules.decision.engine.filters import _extract_candidate_id
from app.modules.decision.engine.pipeline import MAX_EXCLUDED_DETAIL


class MealType(str, Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"


CRITERIA = [
    {"domain": "food", "name": "Giá", "direction": "min", "weight": Decimal("0.4000")},
    {
        "domain": "food",
        "name": "Mức phù hợp nhu cầu/khẩu vị",
        "direction": "max",
        "weight": Decimal("0.3500"),
    },
    {
        "domain": "food",
        "name": "Thời gian chuẩn bị",
        "direction": "min",
        "weight": Decimal("0.2500"),
    },
]


def _food(food_id, name, price=30_000, meal_type="lunch", prep_time=15, ingredients=None):
    return {
        "id": food_id,
        "name": name,
        "price": price,
        "meal_type": meal_type,
        "prep_time": prep_time,
        "ingredients": ingredients if ingredients is not None else [],
        "preference": 80,
    }


class TestExcludedCandidatesLimit(unittest.TestCase):
    """P1 - Danh sách chi tiết bị cắt nhưng total_excluded phải đầy đủ."""

    def test_detail_list_is_capped_but_total_preserved(self) -> None:
        total = MAX_EXCLUDED_DETAIL + 15
        candidates = [
            _food(i, f"Món {i}", price=90_000) for i in range(1, total + 1)
        ]
        result = evaluate_decision(
            candidates=candidates,
            criteria=CRITERIA,
            domain="food",
            budget_max=50_000,
        )

        self.assertEqual(result["total_excluded"], total)
        self.assertEqual(len(result["excluded_candidates"]), MAX_EXCLUDED_DETAIL)
        self.assertEqual(result["excluded_returned_count"], MAX_EXCLUDED_DETAIL)
        self.assertFalse(result["has_valid_candidates"])

    def test_limit_does_not_affect_small_excluded_list(self) -> None:
        candidates = [_food(i, f"Món {i}", price=90_000) for i in range(1, 4)]
        result = evaluate_decision(
            candidates=candidates,
            criteria=CRITERIA,
            domain="food",
            budget_max=50_000,
        )
        self.assertEqual(result["total_excluded"], 3)
        self.assertEqual(len(result["excluded_candidates"]), 3)

    def test_excluded_limit_is_independent_from_valid_limit(self) -> None:
        """limit của valid_candidates không được dùng để cắt excluded_candidates."""
        candidates = [_food(1, "Món hợp lệ", price=30_000)] + [
            _food(i, f"Món loại {i}", price=90_000) for i in range(2, 12)
        ]
        result = evaluate_decision(
            candidates=candidates,
            criteria=CRITERIA,
            domain="food",
            budget_max=50_000,
            limit=1,
        )
        self.assertEqual(result["total_valid"], 1)
        self.assertEqual(result["returned_count"], 1)
        self.assertEqual(result["total_excluded"], 10)
        self.assertEqual(len(result["excluded_candidates"]), 10)


class TestExplainConstraint(unittest.TestCase):
    """P2 - Thông báo giải thích Hard Constraint của Food."""

    def test_price_message(self) -> None:
        _valid, excluded = filter_and_explain_candidates(
            [_food(1, "Món A", price=75_000)], budget_max=50_000
        )
        self.assertIn("vượt quá ngân sách tối đa", excluded[0]["exclusion_reason"])
        self.assertIn("75,000", excluded[0]["exclusion_reason"])

    def test_prep_time_message(self) -> None:
        _valid, excluded = filter_and_explain_candidates(
            [_food(1, "Món A", prep_time=45)], max_prep_time=30
        )
        self.assertIn("vượt quá giới hạn tối đa", excluded[0]["exclusion_reason"])
        self.assertIn("45", excluded[0]["exclusion_reason"])

    def test_meal_type_message(self) -> None:
        _valid, excluded = filter_and_explain_candidates(
            [_food(1, "Món A", meal_type="dinner")], meal_type="lunch"
        )
        self.assertIn("không phù hợp với bữa ăn yêu cầu", excluded[0]["exclusion_reason"])
        self.assertIn("dinner", excluded[0]["exclusion_reason"])

    def test_ingredients_message(self) -> None:
        _valid, excluded = filter_and_explain_candidates(
            [_food(1, "Món A", ingredients=["tôm sú"])], excluded_ingredients=["tôm"]
        )
        self.assertIn("chứa nguyên liệu cần tránh", excluded[0]["exclusion_reason"].lower())

    def test_missing_price_message(self) -> None:
        candidate = _food(1, "Món A")
        candidate["price"] = None
        _valid, excluded = filter_and_explain_candidates(
            [candidate], budget_max=50_000
        )
        self.assertIn("không hợp lệ", excluded[0]["exclusion_reason"].lower())

    def test_unsupported_operator_uses_generic_message(self) -> None:
        """Operator hợp lệ nhưng không có thông báo riêng → dùng message chung."""
        candidate = _food(1, "Món A", price=30_000)
        is_valid, reasons = inspect_candidate(
            candidate, {"price": ("=", 30_000)}, "food"
        )
        self.assertTrue(is_valid)
        self.assertEqual(reasons, [])


class TestEnumMessage(unittest.TestCase):
    """P2 - Enum hiển thị đúng giá trị."""

    def test_enum_actual_value_in_message(self) -> None:
        candidate = _food(1, "Món A", meal_type=MealType.DINNER)
        _valid, excluded = filter_and_explain_candidates(
            [candidate], meal_type="lunch"
        )
        message = excluded[0]["exclusion_reason"]
        self.assertIn("dinner", message)
        self.assertNotIn("MealType.", message)

    def test_enum_expected_value_in_message(self) -> None:
        candidate = _food(1, "Món A", meal_type=MealType.LUNCH)
        _valid, excluded = filter_and_explain_candidates(
            [candidate], meal_type=MealType.DINNER
        )
        message = excluded[0]["exclusion_reason"]
        self.assertIn("dinner", message)
        self.assertNotIn("MealType.", message)

    def test_plain_string_still_works(self) -> None:
        candidate = _food(1, "Món A", meal_type="dinner")
        _valid, excluded = filter_and_explain_candidates(
            [candidate], meal_type="lunch"
        )
        message = excluded[0]["exclusion_reason"]
        self.assertIn("dinner", message)
        self.assertNotIn("MealType.", message)

    def test_enum_comparison_logic_unchanged(self) -> None:
        """Enum vẫn bị lọc đúng (không đổi logic so sánh)."""
        candidate = _food(1, "Món A", meal_type=MealType.LUNCH)
        valid, excluded = filter_and_explain_candidates([candidate], meal_type="lunch")
        self.assertEqual(len(valid), 1)
        self.assertEqual(excluded, [])

        candidate2 = _food(2, "Món B", meal_type=MealType.DINNER)
        valid2, excluded2 = filter_and_explain_candidates([candidate2], meal_type="lunch")
        self.assertEqual(valid2, [])
        self.assertEqual(len(excluded2), 1)


class TestPublicExports(unittest.TestCase):
    """P2 - Các hàm public import được từ package engine."""

    def test_public_functions_are_importable(self) -> None:
        import app.modules.decision.engine as engine

        for name in (
            "evaluate_decision",
            "filter_and_explain_candidates",
            "inspect_candidate",
        ):
            self.assertIn(name, engine.__all__)
            self.assertTrue(callable(getattr(engine, name)))

    def test_evaluate_still_importable(self) -> None:
        import app.modules.decision.engine as engine

        self.assertTrue(callable(engine.evaluate))


class TestCandidateIdFallback(unittest.TestCase):
    """P2 - Không tạo ID giả bằng 0."""

    def test_existing_id_is_preserved(self) -> None:
        self.assertEqual(_extract_candidate_id({"id": 42}), 42)
        self.assertEqual(_extract_candidate_id({"food_id": 7}), 7)

    def test_missing_id_returns_none(self) -> None:
        self.assertIsNone(_extract_candidate_id({"name": "Món A"}))
        self.assertIsNone(_extract_candidate_id({"id": None}))

    def test_blank_string_id_returns_none(self) -> None:
        self.assertIsNone(_extract_candidate_id({"id": "  "}))

    def test_excluded_candidate_without_id_has_none(self) -> None:
        candidate = _food(None, "Món A", price=90_000)
        candidate.pop("id")
        _valid, excluded = filter_and_explain_candidates(
            [candidate], budget_max=50_000
        )
        self.assertIsNone(excluded[0]["id"])
        self.assertEqual(excluded[0]["name"], "Món A")
        self.assertTrue(excluded[0]["exclusion_reason"])

    def test_excluded_candidate_with_id_keeps_real_id(self) -> None:
        _valid, excluded = filter_and_explain_candidates(
            [_food(123, "Món A", price=90_000)], budget_max=50_000
        )
        self.assertEqual(excluded[0]["id"], 123)


if __name__ == "__main__":
    unittest.main()
