"""Kiểm thử tính năng trả kết quả Scoring và thống kê phương án bị loại.

Đáp ứng đầy đủ 8 trường hợp kiểm thử theo yêu cầu:
1. Tất cả phương án đều hợp lệ.
2. Một số phương án hợp lệ, một số phương án bị loại.
3. Tất cả phương án đều bị loại (tuyệt đối không chạy Scoring khi không còn ứng viên).
4. Không có phương án nào được gửi vào.
5. Phương án hợp lệ có đầy đủ total_score, rank và thông tin chi tiết từng tiêu chí.
6. Kiểm tra contribution và total_score có chính xác theo công thức WSM.
7. Kiểm tra thứ hạng khi có hai phương án bằng điểm nhau (tie-break).
8. Kiểm tra lý do bị loại (exclusion_reason) có được trả về chính xác theo quy tắc validation.
"""

import sys
import unittest
from decimal import Decimal
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.modules.decision.engine.calculator import calculate_wsm
from app.modules.decision.engine.filters import filter_and_explain_candidates
from app.modules.decision.engine.pipeline import evaluate_decision
from app.modules.decision.engine.ranking import rank_candidates


class TestScoringAndExclusions(unittest.TestCase):
    def setUp(self) -> None:
        self.food_criteria = [
            {
                "domain": "food",
                "name": "Giá",
                "direction": "min",
                "weight": Decimal("0.4000"),
            },
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

    # --------------------------------------------------------------------------
    # Trường hợp 1: Tất cả phương án đều hợp lệ
    # --------------------------------------------------------------------------
    def test_1_all_candidates_valid(self) -> None:
        """Tất cả phương án đều thỏa mãn điều kiện bắt buộc -> đều được Scoring."""
        candidates = [
            {
                "id": 1,
                "name": "Phở Bò",
                "price": 45000,
                "meal_type": "lunch",
                "prep_time": 15,
                "tags": ["nước", "bò"],
            },
            {
                "id": 2,
                "name": "Cơm Tấm",
                "price": 35000,
                "meal_type": "lunch",
                "prep_time": 10,
                "tags": ["cơm", "sườn"],
            },
            {
                "id": 3,
                "name": "Bánh Mì",
                "price": 25000,
                "meal_type": "lunch",
                "prep_time": 5,
                "tags": ["bánh mì", "nhanh"],
            },
        ]
        result = evaluate_decision(
            candidates=candidates,
            criteria=self.food_criteria,
            domain="food",
            budget_max=50000,
            meal_type="lunch",
            max_prep_time=20,
        )

        self.assertTrue(result["success"])
        self.assertTrue(result["has_valid_candidates"])
        self.assertEqual(result["total_valid"], 3)
        self.assertEqual(result["total_excluded"], 0)
        self.assertEqual(len(result["valid_candidates"]), 3)
        self.assertEqual(len(result["excluded_candidates"]), 0)

        # Kiểm tra tất cả đều có rank từ 1 đến 3
        ranks = [c["rank"] for c in result["valid_candidates"]]
        self.assertEqual(ranks, [1, 2, 3])

    # --------------------------------------------------------------------------
    # Trường hợp 2: Một số phương án hợp lệ, một số phương án bị loại
    # --------------------------------------------------------------------------
    def test_2_some_valid_some_excluded(self) -> None:
        """Một số phương án hợp lệ tiếp tục được tính điểm, các phương án bị loại được thống kê."""
        candidates = [
            {
                "id": 101,
                "name": "Món A (Hợp lệ)",
                "price": 30000,
                "meal_type": "lunch",
                "prep_time": 15,
            },
            {
                "id": 102,
                "name": "Món B (Quá ngân sách)",
                "price": 60000,
                "meal_type": "lunch",
                "prep_time": 15,
            },
            {
                "id": 103,
                "name": "Món C (Sai bữa)",
                "price": 30000,
                "meal_type": "dinner",
                "prep_time": 15,
            },
            {
                "id": 104,
                "name": "Món D (Quá giờ làm)",
                "price": 30000,
                "meal_type": "lunch",
                "prep_time": 45,
            },
        ]
        result = evaluate_decision(
            candidates=candidates,
            criteria=self.food_criteria,
            domain="food",
            budget_max=50000,
            meal_type="lunch",
            max_prep_time=30,
        )

        self.assertTrue(result["has_valid_candidates"])
        self.assertEqual(result["total_valid"], 1)
        self.assertEqual(result["total_excluded"], 3)

        # Phương án hợp lệ duy nhất là Món A
        valid = result["valid_candidates"]
        self.assertEqual(len(valid), 1)
        self.assertEqual(valid[0]["id"], 101)
        self.assertEqual(valid[0]["rank"], 1)

        # 3 phương án bị loại được thống kê
        excluded = result["excluded_candidates"]
        self.assertEqual(len(excluded), 3)
        excluded_ids = [e["id"] for e in excluded]
        self.assertIn(102, excluded_ids)
        self.assertIn(103, excluded_ids)
        self.assertIn(104, excluded_ids)

        for item in excluded:
            self.assertEqual(item["status"], "excluded")
            self.assertTrue(item["is_excluded"])
            self.assertTrue(len(item["exclusion_reason"]) > 0)

    # --------------------------------------------------------------------------
    # Trường hợp 3: Tất cả phương án đều bị loại
    # --------------------------------------------------------------------------
    def test_3_all_candidates_excluded_no_scoring(self) -> None:
        """Khi tất cả đều bị loại: tuyệt đối không chạy Scoring, trả response thông báo rõ ràng."""
        candidates = [
            {
                "id": 1,
                "name": "Lẩu Thái",
                "price": 150000,
                "meal_type": "lunch",
                "prep_time": 30,
            },
            {
                "id": 2,
                "name": "Bò Nướng",
                "price": 120000,
                "meal_type": "lunch",
                "prep_time": 25,
            },
        ]
        result = evaluate_decision(
            candidates=candidates,
            criteria=self.food_criteria,
            domain="food",
            budget_max=50000,  # Cả 2 đều vượt quá 50k
        )

        self.assertTrue(result["success"])
        self.assertFalse(result["has_valid_candidates"])
        self.assertEqual(result["total_valid"], 0)
        self.assertEqual(result["total_excluded"], 2)
        self.assertEqual(result["valid_candidates"], [])
        self.assertEqual(len(result["excluded_candidates"]), 2)
        self.assertIn("không có phương án hợp lệ", result["message"].lower())

        # Kiểm tra lý do bị loại của từng phương án
        for exc in result["excluded_candidates"]:
            self.assertEqual(exc["status"], "excluded")
            self.assertIn("vượt quá ngân sách tối đa", exc["exclusion_reason"].lower())

    # --------------------------------------------------------------------------
    # Trường hợp 4: Không có phương án nào được gửi vào
    # --------------------------------------------------------------------------
    def test_4_empty_candidates_input(self) -> None:
        """Danh sách rỗng ngay từ đầu -> không chạy Scoring, thông báo rõ ràng."""
        result = evaluate_decision(
            candidates=[],
            criteria=self.food_criteria,
            domain="food",
            budget_max=50000,
        )

        self.assertTrue(result["success"])
        self.assertFalse(result["has_valid_candidates"])
        self.assertEqual(result["total_valid"], 0)
        self.assertEqual(result["total_excluded"], 0)
        self.assertEqual(result["valid_candidates"], [])
        self.assertEqual(result["excluded_candidates"], [])
        self.assertIn("không có phương án nào", result["message"].lower())

    # --------------------------------------------------------------------------
    # Trường hợp 5: Phương án hợp lệ có đầy đủ total_score, rank và chi tiết tiêu chí
    # --------------------------------------------------------------------------
    def test_5_valid_candidate_has_complete_scoring_fields(self) -> None:
        """Phương án hợp lệ phải có đủ total_score, rank, normalized_score, weight, contribution."""
        candidates = [
            {
                "id": 1,
                "name": "Món X",
                "price": 30000,
                "preference": 80,
                "prep_time": 15,
            },
            {
                "id": 2,
                "name": "Món Y",
                "price": 20000,
                "preference": 90,
                "prep_time": 10,
            },
        ]
        result = evaluate_decision(
            candidates=candidates,
            criteria=self.food_criteria,
            domain="food",
            budget_max=50000,
        )

        self.assertTrue(result["has_valid_candidates"])
        for cand in result["valid_candidates"]:
            # Yêu cầu A: Có total_score và rank
            self.assertIn("total_score", cand)
            self.assertIn("rank", cand)
            self.assertIsInstance(cand["total_score"], float)
            self.assertIsInstance(cand["rank"], int)

            # Có chi tiết từng tiêu chí
            self.assertIn("criteria_details", cand)
            details = cand["criteria_details"]
            self.assertIn("price", details)
            self.assertIn("preference", details)
            self.assertIn("prep_time", details)

            # Mỗi tiêu chí có normalized_score, weight, contribution
            for crit_info in details.values():
                self.assertIn("normalized_score", crit_info)
                self.assertIn("weight", crit_info)
                self.assertIn("contribution", crit_info)
                self.assertIsInstance(crit_info["weight"], float)
                self.assertIsInstance(crit_info["contribution"], float)

    # --------------------------------------------------------------------------
    # Trường hợp 6: Kiểm tra contribution và total_score chính xác theo công thức WSM
    # --------------------------------------------------------------------------
    def test_6_contribution_and_total_score_accuracy(self) -> None:
        """contribution = weight * normalized_score
        total_score = SUM(contribution).
        """
        # Giả lập 1 ứng viên đã qua scoring với các điểm số xác định
        candidates_scored = [
            {
                "id": 1,
                "name": "Món Chuẩn",
                "criteria_scores": {
                    "price": 40.0,  # weight 0.40 -> contribution = 16.00
                    "preference": 100.0,  # weight 0.35 -> contribution = 35.00
                    "prep_time": 50.0,  # weight 0.25 -> contribution = 12.50
                },
            }
        ]
        calculated = calculate_wsm(candidates_scored, self.food_criteria)
        item = calculated[0]

        # Kiểm tra chi tiết từng tiêu chí
        details = item["criteria_details"]
        self.assertEqual(details["price"]["normalized_score"], 40.0)
        self.assertEqual(details["price"]["weight"], 0.40)
        self.assertEqual(details["price"]["contribution"], 16.00)

        self.assertEqual(details["preference"]["normalized_score"], 100.0)
        self.assertEqual(details["preference"]["weight"], 0.35)
        self.assertEqual(details["preference"]["contribution"], 35.00)

        self.assertEqual(details["prep_time"]["normalized_score"], 50.0)
        self.assertEqual(details["prep_time"]["weight"], 0.25)
        self.assertEqual(details["prep_time"]["contribution"], 12.50)

        # total_score = SUM(contribution) = 16.00 + 35.00 + 12.50 = 63.50
        expected_total = (
            details["price"]["contribution"]
            + details["preference"]["contribution"]
            + details["prep_time"]["contribution"]
        )
        self.assertEqual(expected_total, 63.50)
        self.assertEqual(item["total_score"], 63.50)
        self.assertEqual(item["score"], 63.50)

    # --------------------------------------------------------------------------
    # Trường hợp 7: Kiểm tra thứ hạng khi có hai phương án bằng điểm nhau (tie-break)
    # --------------------------------------------------------------------------
    def test_7_tie_breaking_order(self) -> None:
        """Hòa điểm:
        1. Ưu tiên chi phí thấp hơn
        2. Nếu cùng chi phí -> ưu tiên tên A-Z
        3. Nếu cùng tên -> ưu tiên ID nhỏ hơn.
        """
        candidates = [
            {
                "id": 10,
                "name": "Phở Gà Đắt",
                "price": 60000,
                "score": 50.00,
                "total_score": 50.00,
            },
            {
                "id": 20,
                "name": "Bún Riêu Rẻ",
                "price": 40000,
                "score": 50.00,
                "total_score": 50.00,
            },
        ]
        ranked = rank_candidates(candidates)

        # Bún Riêu Rẻ (40k) rẻ hơn Phở Gà Đắt (60k) -> Bún Riêu đứng rank 1
        self.assertEqual(ranked[0]["name"], "Bún Riêu Rẻ")
        self.assertEqual(ranked[0]["rank"], 1)
        self.assertEqual(ranked[1]["name"], "Phở Gà Đắt")
        self.assertEqual(ranked[1]["rank"], 2)

        # Bằng điểm và bằng giá -> xét tên A-Z
        candidates_same_price = [
            {"id": 1, "name": "Phở Bò", "price": 40000, "score": 50.00},
            {"id": 2, "name": "Bánh Cuốn", "price": 40000, "score": 50.00},
        ]
        ranked_by_name = rank_candidates(candidates_same_price)
        self.assertEqual(ranked_by_name[0]["name"], "Bánh Cuốn")
        self.assertEqual(ranked_by_name[0]["rank"], 1)
        self.assertEqual(ranked_by_name[1]["name"], "Phở Bò")
        self.assertEqual(ranked_by_name[1]["rank"], 2)

        # Bằng điểm, bằng giá, bằng tên -> xét ID tăng dần
        candidates_same_name = [
            {"id": 105, "name": "Bún Chả", "price": 40000, "score": 50.00},
            {"id": 101, "name": "Bún Chả", "price": 40000, "score": 50.00},
        ]
        ranked_by_id = rank_candidates(candidates_same_name)
        self.assertEqual(ranked_by_id[0]["id"], 101)
        self.assertEqual(ranked_by_id[1]["id"], 105)

    # --------------------------------------------------------------------------
    # Trường hợp 8: Kiểm tra lý do bị loại (exclusion_reason) chính xác
    # --------------------------------------------------------------------------
    def test_8_exclusion_reasons_accuracy(self) -> None:
        """Kiểm tra thông điệp giải thích vi phạm cụ thể theo quy tắc validation."""
        candidates = [
            {
                "id": 1,
                "name": "Món Quá Giá",
                "price": 75000,
                "meal_type": "lunch",
                "prep_time": 15,
                "ingredients": ["thịt heo"],
            },
            {
                "id": 2,
                "name": "Món Quá Thời Gian",
                "price": 30000,
                "meal_type": "lunch",
                "prep_time": 45,
                "ingredients": ["thịt bò"],
            },
            {
                "id": 3,
                "name": "Món Sai Bữa Ăn",
                "price": 30000,
                "meal_type": "dinner",
                "prep_time": 15,
                "ingredients": ["rau"],
            },
            {
                "id": 4,
                "name": "Món Chứa Nguyên Liệu Tránh",
                "price": 30000,
                "meal_type": "lunch",
                "prep_time": 15,
                "ingredients": ["tôm sú", "hành lá"],
            },
            {
                "id": 5,
                "name": "Món Vi Phạm Nhiều Điều Kiện",
                "price": 90000,
                "meal_type": "breakfast",
                "prep_time": 60,
                "ingredients": ["tôm"],
            },
            {
                "id": 6,
                "name": "Món Thiếu Giá",
                "price": None,
                "meal_type": "lunch",
                "prep_time": 15,
            },
        ]

        valid, excluded = filter_and_explain_candidates(
            candidates,
            budget_max=50000,
            meal_type="lunch",
            max_prep_time=30,
            excluded_ingredients=["tôm"],
        )

        self.assertEqual(len(valid), 0)
        self.assertEqual(len(excluded), 6)

        exc_map = {item["id"]: item for item in excluded}

        # 1. Quá giá
        self.assertIn("vượt quá ngân sách", exc_map[1]["exclusion_reason"].lower())
        self.assertIn("75,000", exc_map[1]["exclusion_reason"])

        # 2. Quá thời gian
        self.assertIn(
            "vượt quá giới hạn tối đa", exc_map[2]["exclusion_reason"].lower()
        )
        self.assertIn("45", exc_map[2]["exclusion_reason"])

        # 3. Sai bữa ăn
        self.assertIn(
            "không phù hợp với bữa ăn yêu cầu", exc_map[3]["exclusion_reason"].lower()
        )
        self.assertIn("dinner", exc_map[3]["exclusion_reason"])

        # 4. Chứa nguyên liệu tránh
        self.assertIn(
            "chứa nguyên liệu cần tránh", exc_map[4]["exclusion_reason"].lower()
        )
        self.assertIn("tôm", exc_map[4]["exclusion_reason"])

        # 5. Vi phạm nhiều điều kiện -> có danh sách exclusion_reasons >= 3
        self.assertGreaterEqual(len(exc_map[5]["exclusion_reasons"]), 3)

        # 6. Thiếu giá
        self.assertIn("không hợp lệ", exc_map[6]["exclusion_reason"].lower())


if __name__ == "__main__":
    unittest.main()
