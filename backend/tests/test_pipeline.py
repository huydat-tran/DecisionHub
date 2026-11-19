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
from app.modules.decision.engine.pipeline import evaluate
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


if __name__ == "__main__":
    unittest.main()
