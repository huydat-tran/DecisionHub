"""Bộ kiểm thử đối chiếu dữ liệu mẫu WSM tính bằng tay với WSM Engine thực tế.

Thực hiện theo TASK: [DB] Dữ liệu ví dụ WSM để kiểm chứng.
Đối chiếu trực tiếp 6 trường hợp kiểm chứng:
1. Dữ liệu WSM hợp lệ: Tính điểm chính xác (normalized_score, weight, contribution, total_score).
2. Nhiều phương án: Xếp hạng giảm dần (rank).
3. Tiêu chí Benefit và Cost: Chuẩn hóa đúng chiều.
4. Có phương án bị loại: Trả về lý do bị loại (Hard Constraints).
5. Trọng số không hợp lệ: Xử lý theo quy tắc Engine.
6. Không còn phương án hợp lệ: Không thực hiện scoring.
"""

import json
import sys
import unittest
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.modules.decision.engine.calculator import (
    calculate_wsm,
    validate_weights,
)
from app.modules.decision.engine.filters import filter_and_explain_candidates
from app.modules.decision.engine.pipeline import evaluate_decision
from app.modules.decision.engine.ranking import rank_candidates
from app.modules.decision.engine.scoring import (
    normalize_benefit,
    normalize_cost,
    score_candidates,
)

SEED_JSON_PATH = (
    Path(__file__).resolve().parents[1]
    / "sql"
    / "seeds"
    / "wsm_sample_verification.json"
)


class TestWSMVerification(unittest.TestCase):
    """Kiểm chứng kết quả WSM Engine bằng bộ dữ liệu mẫu tính toán bằng tay."""

    @classmethod
    def setUpClass(cls) -> None:
        """Đọc bộ dữ liệu mẫu WSM từ file JSON chuẩn."""
        with open(SEED_JSON_PATH, encoding="utf-8") as f:
            cls.data = json.load(f)

        cls.criteria = cls.data["criteria"]
        cls.candidates = cls.data["candidates"]
        raw_constraints = cls.data["constraints"]
        cls.constraints = {
            k: (v["operator"], v["value"]) for k, v in raw_constraints.items()
        }
        cls.hand_calc = cls.data["hand_calculation_results"]

    def test_01_valid_wsm_calculation(self) -> None:
        """STT 1: Dữ liệu WSM hợp lệ -> Kiểm tra tính điểm chính xác từng số liệu."""
        # Bước lọc
        valid_cands, _ = filter_and_explain_candidates(
            self.candidates, self.constraints, domain="food"
        )
        self.assertEqual(len(valid_cands), 3)

        # Bước chuẩn hóa
        scored = score_candidates(valid_cands, self.criteria, user_preferences=None)

        # Bước tính WSM
        calculated = calculate_wsm(scored, self.criteria)
        self.assertEqual(len(calculated), 3)

        cand_map = {c["id"]: c for c in calculated}

        # 1. Kiểm tra Phương án A (Phở Bò Tái)
        cand_a = cand_map[1]
        self.assertEqual(cand_a["total_score"], 74.17)
        details_a = cand_a["criteria_details"]
        self.assertEqual(details_a["price"]["normalized_score"], 100.0)
        self.assertEqual(details_a["price"]["weight"], 0.4)
        self.assertEqual(details_a["price"]["contribution"], 40.0)

        self.assertEqual(details_a["preference"]["normalized_score"], 50.0)
        self.assertEqual(details_a["preference"]["weight"], 0.35)
        self.assertEqual(details_a["preference"]["contribution"], 17.5)

        self.assertEqual(details_a["prep_time"]["normalized_score"], 66.67)
        self.assertEqual(details_a["prep_time"]["weight"], 0.25)
        self.assertAlmostEqual(
            details_a["prep_time"]["contribution"], 16.6675, places=4
        )

        # 2. Kiểm tra Phương án B (Cơm Sườn Nướng)
        cand_b = cand_map[2]
        self.assertEqual(cand_b["total_score"], 35.0)
        details_b = cand_b["criteria_details"]
        self.assertEqual(details_b["price"]["contribution"], 0.0)
        self.assertEqual(details_b["preference"]["contribution"], 35.0)
        self.assertEqual(details_b["prep_time"]["contribution"], 0.0)

        # 3. Kiểm tra Phương án C (Bún Chả Hà Nội)
        cand_c = cand_map[3]
        self.assertEqual(cand_c["total_score"], 45.0)
        details_c = cand_c["criteria_details"]
        self.assertEqual(details_c["price"]["contribution"], 20.0)
        self.assertEqual(details_c["preference"]["contribution"], 0.0)
        self.assertEqual(details_c["prep_time"]["contribution"], 25.0)

    def test_02_multiple_candidates_ranking(self) -> None:
        """STT 2: Nhiều phương án -> Xếp hạng giảm dần chính xác theo rank tính tay."""
        valid_cands, _ = filter_and_explain_candidates(
            self.candidates, self.constraints, domain="food"
        )
        scored = score_candidates(valid_cands, self.criteria, user_preferences=None)
        calculated = calculate_wsm(scored, self.criteria)
        ranked = rank_candidates(calculated)

        expected_ranks = self.hand_calc["step_5_total_scores_and_ranking"]
        self.assertEqual(len(ranked), len(expected_ranks))

        for idx, expected in enumerate(expected_ranks):
            actual = ranked[idx]
            self.assertEqual(actual["rank"], expected["rank"])
            self.assertEqual(actual["id"], expected["id"])
            self.assertEqual(actual["total_score"], expected["total_score"])

        # Hạng 1 phải là Phương án A, Hạng 2 là C, Hạng 3 là B
        self.assertEqual(ranked[0]["name"], "Phương án A (Phở Bò Tái)")
        self.assertEqual(ranked[1]["name"], "Phương án C (Bún Chả Hà Nội)")
        self.assertEqual(ranked[2]["name"], "Phương án B (Cơm Sườn Nướng)")

    def test_03_benefit_and_cost_normalization(self) -> None:
        """STT 3: Có tiêu chí Benefit và Cost -> Chuẩn hóa đúng chiều."""
        # Kiểm tra hàm chuẩn hóa đơn vị
        # Benefit: value=90 trong khoảng [70, 90] -> 100.0, value=70 -> 0.0
        self.assertEqual(normalize_benefit(90, 70, 90), 100.0)
        self.assertEqual(normalize_benefit(80, 70, 90), 50.0)
        self.assertEqual(normalize_benefit(70, 70, 90), 0.0)

        # Cost: value=30000 trong khoảng [30000, 50000] -> 100.0 (giá rẻ nhất), value=50000 -> 0.0
        self.assertEqual(normalize_cost(30000, 30000, 50000), 100.0)
        self.assertEqual(normalize_cost(40000, 30000, 50000), 50.0)
        self.assertEqual(normalize_cost(50000, 30000, 50000), 0.0)

        # Cost prep_time: value=10 trong [10, 25] -> 100.0 (nhanh nhất), value=25 -> 0.0
        self.assertEqual(normalize_cost(10, 10, 25), 100.0)
        self.assertAlmostEqual(normalize_cost(15, 10, 25), 66.666667, places=4)
        self.assertEqual(normalize_cost(25, 10, 25), 0.0)

    def test_04_excluded_candidate_reason(self) -> None:
        """STT 4: Có phương án bị loại -> Trả về lý do bị loại cụ thể."""
        valid_cands, excluded_cands = filter_and_explain_candidates(
            self.candidates, self.constraints, domain="food"
        )
        self.assertEqual(len(valid_cands), 3)
        self.assertEqual(len(excluded_cands), 1)

        excluded = excluded_cands[0]
        self.assertEqual(excluded["id"], 4)
        self.assertEqual(excluded["name"], "Phương án D (Mì Xào Bò Đặc Biệt)")
        self.assertEqual(excluded["status"], "excluded")
        self.assertTrue(excluded["is_excluded"])

        # Phải nêu rõ cả 2 lý do vi phạm: vượt ngân sách 60k và chứa hành
        reason_str = excluded["exclusion_reason"]
        self.assertIn("60,000", reason_str)
        self.assertIn("hành", reason_str)
        self.assertEqual(len(excluded["exclusion_reasons"]), 2)

    def test_05_invalid_weights_handling(self) -> None:
        """STT 5: Trọng số không hợp lệ -> Xử lý theo quy tắc Engine."""
        # 1. Tổng trọng số khác 1.0 (0.4 + 0.35 + 0.20 = 0.95)
        invalid_sum_criteria = [
            {"name": "Giá", "weight": 0.40},
            {"name": "Mức phù hợp nhu cầu/khẩu vị", "weight": 0.35},
            {"name": "Thời gian chuẩn bị", "weight": 0.20},
        ]
        with self.assertRaises(ValueError) as ctx:
            validate_weights(invalid_sum_criteria)
        self.assertIn("Tổng weight phải bằng 1.0", str(ctx.exception))

        # 2. Trọng số âm (-0.1)
        negative_weight_criteria = [
            {"name": "Giá", "weight": 0.40},
            {"name": "Mức phù hợp nhu cầu/khẩu vị", "weight": 0.70},
            {"name": "Thời gian chuẩn bị", "weight": -0.10},
        ]
        with self.assertRaises(ValueError) as ctx:
            validate_weights(negative_weight_criteria)
        self.assertIn("không được âm", str(ctx.exception))

        # 3. Danh sách trọng số rỗng
        with self.assertRaises(ValueError) as ctx:
            validate_weights([])
        self.assertIn("không được rỗng", str(ctx.exception))

    def test_06_no_valid_candidates_stops_scoring(self) -> None:
        """STT 6: Không còn phương án hợp lệ -> Tuyệt đối không thực hiện scoring."""
        # Ngân sách quá thấp: 15.000đ -> Không có món nào thỏa mãn
        strict_constraints = {
            "price": ("<=", 15000),
        }
        res = evaluate_decision(
            self.candidates,
            self.criteria,
            domain="food",
            constraints=strict_constraints,
        )

        self.assertTrue(res["success"])
        self.assertFalse(res["has_valid_candidates"])
        self.assertEqual(len(res["valid_candidates"]), 0)
        self.assertEqual(res["total_valid"], 0)
        self.assertEqual(len(res["excluded_candidates"]), 4)
        self.assertEqual(res["total_excluded"], 4)
        self.assertIn("điều kiện bắt buộc", res["message"])


if __name__ == "__main__":
    unittest.main()
