"""Integration tests cho toàn bộ luồng Decision Engine:
scoring.py → calculator.py → ranking.py
"""

from decimal import Decimal
from pathlib import Path
import sys
import unittest

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.modules.decision.engine.calculator import calculate_wsm
from app.modules.decision.engine.pipeline import evaluate, evaluate_decision
from app.modules.decision.engine.ranking import rank_candidates
from app.modules.decision.engine.scoring import score_candidates


class TestDecisionEnginePipeline(unittest.TestCase):
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

    def test_scoring_does_not_produce_score_field(self) -> None:
        """score_candidates() chỉ trả criteria_scores, không có trường 'score'."""
        candidates = [
            {"id": 1, "name": "Món A", "price": 30000, "preference": 100, "prep_time": 15},
        ]
        scored = score_candidates(candidates, self.food_criteria)
        self.assertNotIn("score", scored[0])
        self.assertIn("criteria_scores", scored[0])

    def test_end_to_end_three_step_flow(self) -> None:
        """Luồng 3 bước độc lập: scoring → calculator → ranking."""
        candidates = [
            {"id": 101, "name": "Món A", "price": 30000, "preference": 100, "prep_time": 15},
            {"id": 102, "name": "Món B", "price": 40000, "preference": 50, "prep_time": 10},
            {"id": 103, "name": "Món C", "price": 20000, "preference": 50, "prep_time": 20},
        ]

        # Bước 1: Chuẩn hóa điểm từng tiêu chí (không có score)
        scored = score_candidates(candidates, self.food_criteria)
        self.assertNotIn("score", scored[0])

        # Bước 2: Kiểm tra weight và tính tổng WSM
        calculated = calculate_wsm(scored, self.food_criteria)
        self.assertIn("score", calculated[0])

        # Bước 3: Sắp xếp và xếp hạng
        ranked = rank_candidates(calculated)

        # Min-Max với 3 ứng viên này:
        #   price [30k,40k,20k]: min=20k,max=40k → A=50%, B=0%, C=100%
        #   preference [100,50,50]: min=50,max=100 → A=100%, B=0%, C=0%
        #   prep_time [15,10,20]: min=10,max=20 → A=50%, B=100%, C=0%
        # WSM: A=0.4×50+0.35×100+0.25×50=67.50, C=0.4×100=40.00, B=0.25×100=25.00
        self.assertEqual([r["name"] for r in ranked], ["Món A", "Món C", "Món B"])
        self.assertEqual(ranked[0]["score"], 67.50)
        self.assertEqual(ranked[1]["score"], 40.00)
        self.assertEqual(ranked[2]["score"], 25.00)
        self.assertEqual([r["rank"] for r in ranked], [1, 2, 3])

    def test_pipeline_evaluate_helper(self) -> None:
        """Hàm evaluate() trong pipeline.py chạy đúng luồng 3 bước."""
        candidates = [
            {"id": 1, "name": "Món X", "price": 50000, "preference": 80, "prep_time": 20},
            {"id": 2, "name": "Món Y", "price": 30000, "preference": 80, "prep_time": 20},
        ]
        results = evaluate(candidates, self.food_criteria, domain="food")

        # Cả 2 cùng preference=80, prep_time=20 → min=max → 100
        # Món Y rẻ hơn (30k) → tie-break cost → Món Y đứng đầu
        self.assertEqual(results[0]["name"], "Món Y")
        self.assertEqual(results[1]["name"], "Món X")


class TestEvaluateDecisionStatistics(unittest.TestCase):
    """Thống kê total_valid / returned_count phải phản ánh đúng số phương án."""

    def setUp(self) -> None:
        self.food_criteria = [
            {"domain": "food", "name": "Giá", "direction": "min", "weight": Decimal("0.5000")},
            {
                "domain": "food",
                "name": "Mức phù hợp nhu cầu/khẩu vị",
                "direction": "max",
                "weight": Decimal("0.5000"),
            },
        ]
        self.candidates = [
            {"id": i, "name": f"Món {i}", "price": 10_000 * i, "preference": 50, "prep_time": 10}
            for i in range(1, 6)
        ]

    def test_total_valid_counts_all_valid_candidates_before_limit(self) -> None:
        """total_valid phản ánh tổng số ứng viên hợp lệ, không phải số sau limit."""
        result = evaluate_decision(
            candidates=self.candidates,
            criteria=self.food_criteria,
            domain="food",
            limit=2,
        )

        self.assertTrue(result["has_valid_candidates"])
        self.assertEqual(result["total_valid"], 5)
        self.assertEqual(result["returned_count"], 2)
        self.assertEqual(len(result["valid_candidates"]), 2)

    def test_message_mentions_both_valid_total_and_returned_count(self) -> None:
        """Message không được nhầm số ứng viên hợp lệ với số ứng viên trả về."""
        result = evaluate_decision(
            candidates=self.candidates,
            criteria=self.food_criteria,
            domain="food",
            limit=2,
        )

        self.assertIn("5", result["message"])
        self.assertIn("2", result["message"])

    def test_without_limit_valid_and_returned_counts_match(self) -> None:
        """Không có limit thì total_valid == returned_count == len(valid_candidates)."""
        result = evaluate_decision(
            candidates=self.candidates,
            criteria=self.food_criteria,
            domain="food",
        )

        self.assertEqual(result["total_valid"], 5)
        self.assertEqual(result["returned_count"], 5)
        self.assertEqual(result["total_valid"], len(result["valid_candidates"]))

    def test_limit_larger_than_candidate_count(self) -> None:
        """Limit lớn hơn số ứng viên → không bị cắt, hai số bằng nhau."""
        result = evaluate_decision(
            candidates=self.candidates,
            criteria=self.food_criteria,
            domain="food",
            limit=20,
        )

        self.assertEqual(result["total_valid"], 5)
        self.assertEqual(result["returned_count"], 5)

    def test_statistics_present_in_empty_and_excluded_branches(self) -> None:
        """Các nhánh early-return cũng phải có returned_count."""
        empty = evaluate_decision(
            candidates=[],
            criteria=self.food_criteria,
            domain="food",
        )
        self.assertEqual(empty["total_valid"], 0)
        self.assertEqual(empty["returned_count"], 0)

        all_excluded = evaluate_decision(
            candidates=[{"id": 1, "name": "Món A", "price": 999_000, "preference": 50}],
            criteria=self.food_criteria,
            domain="food",
            budget_max=1_000,
        )
        self.assertEqual(all_excluded["total_valid"], 0)
        self.assertEqual(all_excluded["returned_count"], 0)
        self.assertFalse(all_excluded["has_valid_candidates"])


if __name__ == "__main__":
    unittest.main()
