"""Unit tests cho Bước 3 - Criteria Scoring (chuẩn hóa benefit/cost, min=max, dữ liệu thiếu)."""

from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

# Đảm bảo import được `app.*` khi chạy từ root repo hoặc từ `backend/`
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.modules.decision.engine.scoring import (
    EQUAL_RANGE_SCORE,
    normalize_benefit,
    normalize_cost,
    normalize_value,
    score_candidates,
    score_criterion,
)


class TestNormalization(unittest.TestCase):
    def test_normalize_benefit_range(self) -> None:
        self.assertEqual(normalize_benefit(0, 0, 100), 0.0)
        self.assertEqual(normalize_benefit(50, 0, 100), 50.0)
        self.assertEqual(normalize_benefit(100, 0, 100), 100.0)
        self.assertAlmostEqual(normalize_benefit(3, 1, 5), 50.0)

    def test_normalize_cost_range(self) -> None:
        self.assertEqual(normalize_cost(10_000, 10_000, 50_000), 100.0)
        self.assertEqual(normalize_cost(30_000, 10_000, 50_000), 50.0)
        self.assertEqual(normalize_cost(50_000, 10_000, 50_000), 0.0)

    def test_min_equals_max_returns_equal_range_score(self) -> None:
        self.assertEqual(normalize_benefit(42, 42, 42), EQUAL_RANGE_SCORE)
        self.assertEqual(normalize_cost(42, 42, 42), EQUAL_RANGE_SCORE)

    def test_normalize_value_missing_returns_none(self) -> None:
        self.assertIsNone(normalize_value(None, 0, 100, "benefit"))
        self.assertIsNone(normalize_value(True, 0, 100, "cost"))
        self.assertIsNone(normalize_value(float("nan"), 0, 100, "min"))
        self.assertIsNone(normalize_value(float("inf"), 0, 100, "max"))
        self.assertIsNone(normalize_value(float("-inf"), 0, 100, "cost"))
        self.assertIsNone(normalize_value("", 0, 100, "benefit"))
        self.assertIsNone(normalize_value("abc", 0, 100, "cost"))

    def test_normalize_value_numeric_string_and_decimal(self) -> None:
        self.assertEqual(normalize_value(" 50 ", 0, 100, "benefit"), 50.0)
        self.assertEqual(normalize_value(Decimal("30000"), 10_000, 50_000, "cost"), 50.0)

    def test_invalid_direction_or_bounds_raises(self) -> None:
        with self.assertRaises(ValueError):
            normalize_value(10, 0, 100, "unknown")
        with self.assertRaises(ValueError):
            normalize_benefit(10, 100, 0)
        with self.assertRaises(ValueError):
            normalize_cost(10, 100, 0)


class TestScoreCriterion(unittest.TestCase):
    def test_score_criterion_handles_missing_without_imputing(self) -> None:
        # min=10, max=30 (None không tham gia min/max và giữ nguyên None)
        scores = score_criterion([10, None, 30, 20], "cost")
        self.assertEqual(scores, [100.0, None, 0.0, 50.0])

    def test_score_criterion_all_equal_with_missing(self) -> None:
        scores = score_criterion([25_000, None, 25_000], "min")
        self.assertEqual(scores, [EQUAL_RANGE_SCORE, None, EQUAL_RANGE_SCORE])

    def test_score_criterion_all_missing(self) -> None:
        scores = score_criterion([None, None], "benefit")
        self.assertEqual(scores, [None, None])


class TestScoreCandidatesFood(unittest.TestCase):
    def setUp(self) -> None:
        self.food_criteria = [
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

    def test_empty_candidates(self) -> None:
        self.assertEqual(score_candidates([], self.food_criteria), [])

    def test_food_criteria_scoring_benefit_cost_and_missing(self) -> None:
        candidates = [
            {"id": 1, "name": "Phở bò", "price": 40_000, "preference": 80, "prep_time": 10},
            {"id": 2, "name": "Bún chả", "price": 60_000, "preference": 40, "prep_time": 20},
            {"id": 3, "name": "Cơm tấm", "price": 50_000, "preference": 60, "prep_time": None},
        ]
        scored = score_candidates(candidates, self.food_criteria)

        # Món 1: price=100, preference=100, prep_time=100 -> 100.0
        self.assertEqual(scored[0]["criteria_scores"], {"price": 100.0, "preference": 100.0, "prep_time": 100.0})
        self.assertEqual(scored[0]["score"], 100.0)

        # Món 2: price=0, preference=0, prep_time=0 -> 0.0
        self.assertEqual(scored[1]["criteria_scores"], {"price": 0.0, "preference": 0.0, "prep_time": 0.0})
        self.assertEqual(scored[1]["score"], 0.0)

        # Món 3: price=50, preference=50, prep_time=None (không tự suy diễn) -> 0.4*50 + 0.35*50 = 37.5
        self.assertEqual(scored[2]["criteria_scores"], {"price": 50.0, "preference": 50.0, "prep_time": None})
        self.assertEqual(scored[2]["score"], 37.5)
        # Không mutate dict gốc
        self.assertNotIn("criteria_scores", candidates[2])

    def test_single_candidate_min_equals_max(self) -> None:
        candidates = [{"id": 1, "name": "Bánh mì", "price": 25_000, "preference": 100, "prep_time": 5}]
        scored = score_candidates(candidates, self.food_criteria)
        self.assertEqual(
            scored[0]["criteria_scores"],
            {"price": EQUAL_RANGE_SCORE, "preference": EQUAL_RANGE_SCORE, "prep_time": EQUAL_RANGE_SCORE},
        )
        self.assertEqual(scored[0]["score"], 100.0)

    def test_multiple_candidates_min_equals_max(self) -> None:
        candidates = [
            {"id": 1, "name": "Món A", "price": 40_000, "preference": 80, "prep_time": 15},
            {"id": 2, "name": "Món B", "price": 40_000, "preference": 80, "prep_time": 15},
        ]
        scored = score_candidates(candidates, self.food_criteria)
        for item in scored:
            self.assertEqual(
                item["criteria_scores"],
                {"price": EQUAL_RANGE_SCORE, "preference": EQUAL_RANGE_SCORE, "prep_time": EQUAL_RANGE_SCORE},
            )
            self.assertEqual(item["score"], 100.0)

    def test_all_candidates_missing_one_criterion(self) -> None:
        candidates = [
            {"id": 1, "price": 30_000, "preference": 80, "prep_time": None},
            {"id": 2, "price": 50_000, "preference": 40, "prep_time": None},
        ]
        scored = score_candidates(candidates, self.food_criteria)
        self.assertEqual(scored[0]["criteria_scores"], {"price": 100.0, "preference": 100.0, "prep_time": None})
        self.assertEqual(scored[0]["score"], 75.0)
        self.assertEqual(scored[1]["criteria_scores"], {"price": 0.0, "preference": 0.0, "prep_time": None})
        self.assertEqual(scored[1]["score"], 0.0)

    def test_invalid_weight_raises_value_error(self) -> None:
        bad_criteria = [{"domain": "food", "name": "Giá", "direction": "min", "weight": -0.5}]
        with self.assertRaises(ValueError):
            score_candidates([{"id": 1, "price": 20_000}], bad_criteria)

    def test_travel_criteria_mapping_and_object_candidate(self) -> None:
        travel_criteria = [
            {"domain": "travel", "name": "cost", "direction": "min", "weight": 0.4},
            {"domain": "travel", "name": "duration", "direction": "min", "weight": 0.3},
            {"domain": "travel", "name": "activities", "direction": "max", "weight": 0.3},
        ]
        candidates = [
            SimpleNamespace(id=1, estimated_cost=300_000, estimated_duration=4.0, activities=90),
            SimpleNamespace(id=2, estimated_cost=700_000, estimated_duration=8.0, activities=50),
        ]
        scored = score_candidates(candidates, travel_criteria)
        self.assertEqual(scored[0]["score"], 100.0)
        self.assertEqual(scored[1]["score"], 0.0)


if __name__ == "__main__":
    unittest.main()
