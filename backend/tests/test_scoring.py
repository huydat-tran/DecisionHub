"""Unit tests cho Bước 3 - Criteria Scoring (chuẩn hóa benefit/cost, min=max, dữ liệu thiếu)."""

from decimal import Decimal
from pathlib import Path
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

        # score_candidates() chỉ chuẩn hóa, không tính tổng WSM
        self.assertNotIn("score", scored[0])

        # Món 1: price=100, preference=100, prep_time=100
        self.assertEqual(scored[0]["criteria_scores"], {"price": 100.0, "preference": 100.0, "prep_time": 100.0})

        # Món 2: price=0, preference=0, prep_time=0
        self.assertEqual(scored[1]["criteria_scores"], {"price": 0.0, "preference": 0.0, "prep_time": 0.0})

        # Món 3: price=50, preference=50, prep_time=None (không tự suy diễn)
        self.assertEqual(scored[2]["criteria_scores"], {"price": 50.0, "preference": 50.0, "prep_time": None})

        # Không mutate dict gốc
        self.assertNotIn("criteria_scores", candidates[2])

    def test_single_candidate_min_equals_max(self) -> None:
        candidates = [{"id": 1, "name": "Bánh mì", "price": 25_000, "preference": 100, "prep_time": 5}]
        scored = score_candidates(candidates, self.food_criteria)
        self.assertEqual(
            scored[0]["criteria_scores"],
            {"price": EQUAL_RANGE_SCORE, "preference": EQUAL_RANGE_SCORE, "prep_time": EQUAL_RANGE_SCORE},
        )
        # Không có trường score — tính score là việc của calculator
        self.assertNotIn("score", scored[0])


if __name__ == "__main__":
    unittest.main()
