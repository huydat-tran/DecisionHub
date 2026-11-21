"""Unit tests toàn diện cho Decision Engine - DecisionHub.

Bao gồm 7 mục tiêu kiểm thử:
1. Filtering: Lọc các phương án không hợp lệ.
2. Normalization: Chuẩn hóa điểm số của các tiêu chí (Benefit, Cost, Min=Max, Dữ liệu không hợp lệ).
3. Total Weights: Kiểm tra tổng trọng số (bằng 1, nhỏ hơn 1, lớn hơn 1, bằng 0, âm, rỗng/không hợp lệ).
4. WSM Score: Tính tổng điểm theo công thức WSM = Σ(weight × normalized_score).
5. Ranking & Tie-break: Thứ hạng phương án, tie-break 3 cấp (cost -> name -> id), ổn định (stable).
6. Explanation: Kiểm tra kết quả giải thích (total_score, rank, normalized_score, weight, contribution, lý do bị loại).
7. End-to-End Pipeline & Service Integration: Luồng tổng thể, chặn scoring khi không còn ứng viên hợp lệ.
"""

import sys
import unittest
from decimal import Decimal
from enum import Enum
from pathlib import Path
from unittest.mock import patch

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.modules.decision.decision_response import (
    AppliedFilters,
    CriteriaScores,
    CriterionDetail,
    DecisionResponse,
    ExcludedOptionResponse,
    RecommendedFoodResponse,
)
from app.modules.decision.engine.calculator import (
    calculate_food_wsm,
    calculate_preference_score,
    calculate_prep_time_score,
    calculate_price_score,
    calculate_wsm,
    validate_weights,
)
from app.modules.decision.engine.filters import (
    filter_and_explain_candidates,
    filter_candidates,
    passes_hard_constraints,
)
from app.modules.decision.engine.pipeline import evaluate, evaluate_decision
from app.modules.decision.engine.ranking import rank_candidates
from app.modules.decision.engine.scoring import (
    EQUAL_RANGE_SCORE,
    NEUTRAL_PREFERENCE_SCORE,
    normalize_benefit,
    normalize_cost,
    normalize_value,
    score_criterion,
    score_preference,
)


class MealTypeEnum(str, Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"


# ==============================================================================
# 1. FILTERING UNIT TESTS
# ==============================================================================


class TestDecisionEngineFiltering(unittest.TestCase):
    """Kiểm tra chức năng lọc điều kiện bắt buộc (Filtering & Hard Constraints)."""

    def setUp(self) -> None:
        self.food_candidates = [
            {
                "id": 1,
                "name": "Phở Bò Tái",
                "price": 45000,
                "meal_type": "lunch",
                "prep_time": 15,
                "ingredients": ["thịt bò", "bánh phở", "hành lá"],
            },
            {
                "id": 2,
                "name": "Cơm Sườn Nướng",
                "price": 35000,
                "meal_type": "lunch",
                "prep_time": 10,
                "ingredients": ["sườn heo", "cơm", "dưa leo"],
            },
            {
                "id": 3,
                "name": "Bánh Mì Chả",
                "price": 25000,
                "meal_type": "breakfast",
                "prep_time": 5,
                "ingredients": ["bánh mì", "chả lụa", "dưa leo"],
            },
            {
                "id": 4,
                "name": "Bún Đậu Mắm Tôm",
                "price": 55000,
                "meal_type": "lunch",
                "prep_time": 20,
                "ingredients": ["bún", "đậu hũ", "mắm tôm", "thịt luộc"],
            },
            {
                "id": 5,
                "name": "Lẩu Thái Hải Sản",
                "price": 120000,
                "meal_type": "dinner",
                "prep_time": 40,
                "ingredients": ["tôm sú", "mực", "nấm", "nước lẩu"],
            },
        ]

    def test_filtering_all_candidates_valid(self) -> None:
        """Trường hợp 1: Tất cả phương án đều hợp lệ khi điều kiện nới lỏng."""
        candidates = self.food_candidates[:3]  # Phở Bò, Cơm Sườn, Bánh Mì
        valid, excluded = filter_and_explain_candidates(
            candidates,
            budget_max=100000,
            max_prep_time=30,
        )
        self.assertEqual(len(valid), 3)
        self.assertEqual(len(excluded), 0)
        self.assertEqual([c["id"] for c in valid], [1, 2, 3])

    def test_filtering_some_candidates_invalid(self) -> None:
        """Trường hợp 2: Có một số phương án hợp lệ và một số phương án không hợp lệ."""
        # Ngân sách 50k, bữa trưa, thời gian tối đa 25p, tránh mắm tôm
        valid, excluded = filter_and_explain_candidates(
            self.food_candidates,
            budget_max=50000,
            meal_type="lunch",
            max_prep_time=25,
            excluded_ingredients=["mắm tôm"],
        )
        # Hợp lệ:
        # id 1 (Phở Bò): 45k <= 50k, lunch, 15p <= 25p, không mắm tôm -> OK
        # id 2 (Cơm Sườn): 35k <= 50k, lunch, 10p <= 25p, không mắm tôm -> OK
        self.assertEqual(len(valid), 2)
        valid_ids = [c["id"] for c in valid]
        self.assertEqual(valid_ids, [1, 2])

        # Bị loại:
        # id 3 (Bánh Mì): meal_type=breakfast != lunch
        # id 4 (Bún Đậu): price=55k > 50k VÀ chứa mắm tôm
        # id 5 (Lẩu Thái): price=120k > 50k, meal_type=dinner != lunch, prep_time=40p > 25p
        self.assertEqual(len(excluded), 3)
        excluded_ids = [e["id"] for e in excluded]
        self.assertIn(3, excluded_ids)
        self.assertIn(4, excluded_ids)
        self.assertIn(5, excluded_ids)

        for item in excluded:
            self.assertEqual(item["status"], "excluded")
            self.assertTrue(item["is_excluded"])
            self.assertIsInstance(item["exclusion_reason"], str)
            self.assertTrue(len(item["exclusion_reason"]) > 0)

    def test_filtering_all_candidates_invalid(self) -> None:
        """Trường hợp 3: Tất cả phương án đều không hợp lệ."""
        # Ngân sách 20k -> tất cả món đều > 20k
        valid, excluded = filter_and_explain_candidates(
            self.food_candidates,
            budget_max=20000,
        )
        self.assertEqual(len(valid), 0)
        self.assertEqual(len(excluded), len(self.food_candidates))

    def test_filtering_stops_scoring_when_no_valid_candidates(self) -> None:
        """Trường hợp 4: Tuyệt đối KHÔNG được chạy Scoring khi không còn phương án hợp lệ."""
        criteria = [
            {
                "domain": "food",
                "name": "Giá",
                "direction": "min",
                "weight": Decimal("0.40"),
            },
            {
                "domain": "food",
                "name": "Mức phù hợp nhu cầu/khẩu vị",
                "direction": "max",
                "weight": Decimal("0.35"),
            },
            {
                "domain": "food",
                "name": "Thời gian chuẩn bị",
                "direction": "min",
                "weight": Decimal("0.25"),
            },
        ]
        with patch(
            "app.modules.decision.engine.pipeline.score_candidates"
        ) as mock_score:
            result = evaluate_decision(
                candidates=self.food_candidates,
                criteria=criteria,
                domain="food",
                budget_max=10000,  # Tất cả đều bị loại
            )

            # Khẳng định score_candidates không bao giờ được gọi
            mock_score.assert_not_called()

            self.assertTrue(result["success"])
            self.assertFalse(result["has_valid_candidates"])
            self.assertEqual(result["total_valid"], 0)
            self.assertEqual(result["total_excluded"], len(self.food_candidates))
            self.assertEqual(result["valid_candidates"], [])
            self.assertIn("không có phương án hợp lệ", result["message"].lower())

    def test_filtering_exclusion_reasons_details(self) -> None:
        """Trường hợp 5: Kiểm tra nội dung chi tiết lý do phương án bị loại."""
        candidates = [
            {
                "id": 10,
                "name": "Món Đắt",
                "price": 80000,
                "meal_type": "lunch",
                "prep_time": 10,
            },
            {
                "id": 20,
                "name": "Món Lâu",
                "price": 30000,
                "meal_type": "lunch",
                "prep_time": 60,
            },
            {
                "id": 30,
                "name": "Món Sai Bữa",
                "price": 30000,
                "meal_type": "dinner",
                "prep_time": 10,
            },
            {
                "id": 40,
                "name": "Món Dị Ứng",
                "price": 30000,
                "meal_type": "lunch",
                "prep_time": 10,
                "ingredients": ["đậu phộng"],
            },
            {
                "id": 50,
                "name": "Món Thiếu Giá",
                "price": None,
                "meal_type": "lunch",
                "prep_time": 10,
            },
            {
                "id": 60,
                "name": "Món Vi Phạm Nhiều",
                "price": 90000,
                "meal_type": "dinner",
                "prep_time": 50,
            },
        ]

        _, excluded = filter_and_explain_candidates(
            candidates,
            budget_max=50000,
            meal_type="lunch",
            max_prep_time=30,
            excluded_ingredients=["đậu phộng"],
        )

        exc_map = {item["id"]: item for item in excluded}

        # 1. Lý do vượt ngân sách
        self.assertIn(
            "vượt quá ngân sách tối đa", exc_map[10]["exclusion_reason"].lower()
        )
        self.assertIn("80,000", exc_map[10]["exclusion_reason"])

        # 2. Lý do vượt thời gian chuẩn bị
        self.assertIn(
            "vượt quá giới hạn tối đa", exc_map[20]["exclusion_reason"].lower()
        )
        self.assertIn("60", exc_map[20]["exclusion_reason"])

        # 3. Lý do sai bữa ăn
        self.assertIn(
            "không phù hợp với bữa ăn yêu cầu", exc_map[30]["exclusion_reason"].lower()
        )
        self.assertIn("dinner", exc_map[30]["exclusion_reason"])

        # 4. Lý do chứa nguyên liệu cần tránh
        self.assertIn(
            "chứa nguyên liệu cần tránh", exc_map[40]["exclusion_reason"].lower()
        )
        self.assertIn("đậu phộng", exc_map[40]["exclusion_reason"])

        # 5. Lý do thiếu giá hoặc giá không hợp lệ
        self.assertIn(
            "không hợp lệ hoặc thiếu", exc_map[50]["exclusion_reason"].lower()
        )

        # 6. Vi phạm nhiều điều kiện có danh sách exclusion_reasons
        self.assertGreaterEqual(len(exc_map[60]["exclusion_reasons"]), 3)
        self.assertIn(";", exc_map[60]["exclusion_reason"])

    def test_filter_candidates_simple_function(self) -> None:
        """Kiểm tra hàm filter_candidates trả về danh sách thuần các phần tử thỏa mãn."""
        valid_only = filter_candidates(self.food_candidates, budget_max=40000)
        self.assertEqual([c["id"] for c in valid_only], [2, 3])

    def test_passes_hard_constraints_single_item(self) -> None:
        """Kiểm tra passes_hard_constraints cho từng ứng viên đơn lẻ."""
        good = {"id": 1, "price": 30000, "meal_type": "lunch"}
        bad = {"id": 2, "price": 60000, "meal_type": "lunch"}
        self.assertTrue(
            passes_hard_constraints(good, budget_max=50000, meal_type="lunch")
        )
        self.assertFalse(
            passes_hard_constraints(bad, budget_max=50000, meal_type="lunch")
        )


# ==============================================================================
# 2. NORMALIZATION UNIT TESTS
# ==============================================================================


class TestDecisionEngineNormalization(unittest.TestCase):
    """Kiểm tra chuẩn hóa điểm số tiêu chí (Normalization: Benefit, Cost, Min=Max, Dữ liệu lỗi)."""

    def test_normalization_benefit_formula_correctness(self) -> None:
        """Chuẩn hóa tiêu chí Benefit theo công thức 100 * (val - min) / (max - min)."""
        # min = 10, max = 50
        # val = 10 -> 0.0
        # val = 30 -> 100 * (30 - 10) / 40 = 50.0
        # val = 50 -> 100.0
        self.assertAlmostEqual(normalize_benefit(10, 10, 50), 0.0)
        self.assertAlmostEqual(normalize_benefit(30, 10, 50), 50.0)
        self.assertAlmostEqual(normalize_benefit(50, 10, 50), 100.0)
        self.assertAlmostEqual(normalize_benefit(20, 10, 50), 25.0)

    def test_normalization_benefit_clamping(self) -> None:
        """Tiêu chí Benefit: giá trị vượt biên ngoài được clamp vào [0.0, 100.0]."""
        self.assertEqual(normalize_benefit(5, 10, 50), 0.0)
        self.assertEqual(normalize_benefit(60, 10, 50), 100.0)

    def test_normalization_cost_formula_correctness(self) -> None:
        """Chuẩn hóa tiêu chí Cost theo công thức 100 * (max - val) / (max - min)."""
        # min = 20000, max = 100000
        # val = 20000 (rẻ nhất) -> 100.0
        # val = 60000 (ở giữa) -> 100 * (100k - 60k) / 80k = 50.0
        # val = 100000 (đắt nhất) -> 0.0
        self.assertAlmostEqual(normalize_cost(20000, 20000, 100000), 100.0)
        self.assertAlmostEqual(normalize_cost(60000, 20000, 100000), 50.0)
        self.assertAlmostEqual(normalize_cost(100000, 20000, 100000), 0.0)
        self.assertAlmostEqual(normalize_cost(40000, 20000, 100000), 75.0)

    def test_normalization_cost_clamping(self) -> None:
        """Tiêu chí Cost: giá trị vượt biên ngoài được clamp vào [0.0, 100.0]."""
        self.assertEqual(normalize_cost(10000, 20000, 100000), 100.0)
        self.assertEqual(normalize_cost(120000, 20000, 100000), 0.0)

    def test_normalization_equal_min_max_returns_equal_range_score(self) -> None:
        """Khi min == max (tất cả giá trị bằng nhau), trả về EQUAL_RANGE_SCORE (100.0)."""
        self.assertEqual(normalize_benefit(45, 45, 45), EQUAL_RANGE_SCORE)
        self.assertEqual(normalize_cost(45, 45, 45), EQUAL_RANGE_SCORE)
        self.assertEqual(normalize_benefit(0, 0, 0), EQUAL_RANGE_SCORE)

    def test_normalization_score_criterion_with_equal_values(self) -> None:
        """score_criterion với dãy giá trị bằng nhau -> tất cả nhận 100.0."""
        scores_cost = score_criterion([50000, 50000, 50000], "cost")
        self.assertEqual(scores_cost, [100.0, 100.0, 100.0])

        scores_benefit = score_criterion([80, 80], "benefit")
        self.assertEqual(scores_benefit, [100.0, 100.0])

    def test_normalization_invalid_data_inputs(self) -> None:
        """Kiểm tra xử lý các dữ liệu đầu vào không hợp lệ."""
        # 1. min_val > max_val -> raise ValueError
        with self.assertRaises(ValueError):
            normalize_benefit(10, 50, 20)
        with self.assertRaises(ValueError):
            normalize_cost(10, 50, 20)

        # 2. direction không hợp lệ -> raise ValueError
        with self.assertRaises(ValueError):
            normalize_value(10, 0, 100, "invalid_direction")

        # 3. Giá trị thiếu hoặc không phải số -> trả về None (không tự suy diễn điểm)
        self.assertIsNone(normalize_value(None, 0, 100, "benefit"))
        self.assertIsNone(normalize_value(True, 0, 100, "cost"))
        self.assertIsNone(normalize_value(False, 0, 100, "benefit"))
        self.assertIsNone(normalize_value(float("nan"), 0, 100, "cost"))
        self.assertIsNone(normalize_value("chuỗi_không_hợp_lệ", 0, 100, "cost"))

        # 4. score_criterion với dãy chứa None: giữ nguyên None cho phần tử thiếu
        scores = score_criterion([20, None, 60, "abc"], "cost")
        # min=20, max=60 -> 20 -> 100.0, 60 -> 0.0, None -> None, 'abc' -> None
        self.assertEqual(scores, [100.0, None, 0.0, None])

        # 5. score_criterion khi toàn bộ dữ liệu bị thiếu
        self.assertEqual(score_criterion([None, None], "benefit"), [None, None])

    def test_preference_scoring_behavior(self) -> None:
        """Kiểm tra hàm chấm điểm sở thích (score_preference)."""
        # Trùng 2 / 2 tag -> 1.0 (quy đổi 100 điểm)
        self.assertAlmostEqual(score_preference(["bò", "cay"], ["bò", "cay"]), 1.0)
        # Trùng 1 / 2 tag -> 0.5 (quy đổi 50 điểm)
        self.assertAlmostEqual(score_preference(["bò", "ngọt"], ["bò", "cay"]), 0.5)
        # Không trùng tag nào -> 0.0
        self.assertAlmostEqual(score_preference(["gà"], ["bò", "cay"]), 0.0)
        # Người dùng không chọn tag nào -> NEUTRAL_PREFERENCE_SCORE (0.5)
        self.assertEqual(score_preference(["bò"], None), NEUTRAL_PREFERENCE_SCORE)
        self.assertEqual(score_preference(["bò"], []), NEUTRAL_PREFERENCE_SCORE)
        # Ứng viên không có tag trong khi người dùng có chọn -> 0.0
        self.assertEqual(score_preference(None, ["bò"]), 0.0)


# ==============================================================================
# 3. TOTAL WEIGHTS UNIT TESTS
# ==============================================================================


class TestDecisionEngineTotalWeights(unittest.TestCase):
    """Kiểm tra tính hợp lệ của trọng số (Total Weights Validation)."""

    def test_weights_sum_equals_one_valid_list(self) -> None:
        """Tổng trọng số đúng bằng 1.0 dạng danh sách tiêu chí."""
        criteria = [
            {"name": "Giá", "weight": Decimal("0.4000")},
            {"name": "Mức phù hợp nhu cầu/khẩu vị", "weight": Decimal("0.3500")},
            {"name": "Thời gian chuẩn bị", "weight": Decimal("0.2500")},
        ]
        result = validate_weights(criteria)
        self.assertAlmostEqual(result["price"], 0.40)
        self.assertAlmostEqual(result["preference"], 0.35)
        self.assertAlmostEqual(result["prep_time"], 0.25)
        self.assertAlmostEqual(sum(result.values()), 1.0)

    def test_weights_sum_equals_one_valid_dict(self) -> None:
        """Tổng trọng số đúng bằng 1.0 dạng dictionary trực tiếp."""
        weights_dict = {"price": 0.50, "preference": 0.30, "prep_time": 0.20}
        result = validate_weights(weights_dict)
        self.assertEqual(result["price"], 0.50)
        self.assertEqual(result["preference"], 0.30)
        self.assertEqual(result["prep_time"], 0.20)
        self.assertAlmostEqual(sum(result.values()), 1.0)

    def test_weights_sum_less_than_one_raises_value_error(self) -> None:
        """Tổng trọng số nhỏ hơn 1.0 phải raise ValueError thông báo rõ ràng."""
        criteria = [
            {"name": "price", "weight": 0.4},
            {"name": "preference", "weight": 0.3},
            {"name": "prep_time", "weight": 0.2},  # Tổng = 0.9 < 1.0
        ]
        with self.assertRaises(ValueError) as ctx:
            validate_weights(criteria)
        self.assertIn("1.0", str(ctx.exception))
        self.assertIn("Tổng weight phải bằng 1.0", str(ctx.exception))

    def test_weights_sum_greater_than_one_raises_value_error(self) -> None:
        """Tổng trọng số lớn hơn 1.0 phải raise ValueError."""
        criteria = {
            "price": 0.5,
            "preference": 0.4,
            "prep_time": 0.3,
        }  # Tổng = 1.2 > 1.0
        with self.assertRaises(ValueError) as ctx:
            validate_weights(criteria)
        self.assertIn("1.0", str(ctx.exception))

    def test_weights_zero_weight_allowed_when_sum_is_one(self) -> None:
        """Trọng số bằng 0.0 được chấp nhận nếu tổng vẫn bằng 1.0."""
        criteria = {"price": 0.0, "preference": 0.6, "prep_time": 0.4}
        result = validate_weights(criteria)
        self.assertEqual(result["price"], 0.0)
        self.assertEqual(result["preference"], 0.6)
        self.assertEqual(result["prep_time"], 0.4)
        self.assertAlmostEqual(sum(result.values()), 1.0)

    def test_weights_negative_weight_raises_value_error(self) -> None:
        """Trọng số âm phải raise ValueError không cho phép."""
        criteria = [
            {"name": "price", "weight": -0.2},
            {"name": "preference", "weight": 0.8},
            {"name": "prep_time", "weight": 0.4},
        ]
        with self.assertRaises(ValueError) as ctx:
            validate_weights(criteria)
        self.assertIn("không được âm", str(ctx.exception).lower())

    def test_weights_empty_criteria_raises_value_error(self) -> None:
        """Trường hợp không có trọng số (danh sách hoặc dict rỗng) phải raise ValueError."""
        with self.assertRaises(ValueError) as ctx_list:
            validate_weights([])
        self.assertIn("không được rỗng", str(ctx_list.exception))

        with self.assertRaises(ValueError) as ctx_dict:
            validate_weights({})
        self.assertIn("không được rỗng", str(ctx_dict.exception))

    def test_weights_invalid_type_raises_value_error(self) -> None:
        """Trọng số chứa kiểu dữ liệu không hợp lệ (None, bool, NaN, chuỗi ký tự)."""
        for invalid in (None, True, False, float("nan"), "abc"):
            with self.subTest(weight=invalid), self.assertRaises(ValueError):
                validate_weights({"price": invalid, "preference": 1.0})


# ==============================================================================
# 4. WSM SCORE UNIT TESTS
# ==============================================================================


class TestDecisionEngineWSMScore(unittest.TestCase):
    """Kiểm tra cách tính tổng điểm theo công thức Weighted Sum Model (WSM)."""

    def setUp(self) -> None:
        self.weights = {"price": 0.40, "preference": 0.35, "prep_time": 0.25}

    def test_wsm_score_formula_calculation_accuracy(self) -> None:
        """Tính tổng điểm đúng theo công thức: total_score = Σ(weight × normalized_score)."""
        # Giả sử điểm chuẩn hóa:
        # price = 80.0 (w=0.40) -> contribution = 0.40 * 80.0 = 32.0
        # preference = 60.0 (w=0.35) -> contribution = 0.35 * 60.0 = 21.0
        # prep_time = 40.0 (w=0.25) -> contribution = 0.25 * 40.0 = 10.0
        # total_score = 32.0 + 21.0 + 10.0 = 63.0
        candidates = [
            {
                "id": 1,
                "name": "Món Thử Nghiệm",
                "criteria_scores": {
                    "price": 80.0,
                    "preference": 60.0,
                    "prep_time": 40.0,
                },
            }
        ]
        calculated = calculate_wsm(candidates, self.weights)
        item = calculated[0]

        self.assertEqual(item["criteria_details"]["price"]["contribution"], 32.0)
        self.assertEqual(item["criteria_details"]["preference"]["contribution"], 21.0)
        self.assertEqual(item["criteria_details"]["prep_time"]["contribution"], 10.0)
        self.assertEqual(item["total_score"], 63.0)
        self.assertEqual(item["score"], 63.0)

    def test_wsm_score_multiple_candidates(self) -> None:
        """Kiểm tra tính điểm chính xác cho nhiều phương án cùng lúc."""
        candidates = [
            {
                "id": 1,
                "name": "Món Hoàn Hảo",
                "criteria_scores": {
                    "price": 100.0,
                    "preference": 100.0,
                    "prep_time": 100.0,
                },
            },
            {
                "id": 2,
                "name": "Món Kém",
                "criteria_scores": {"price": 0.0, "preference": 0.0, "prep_time": 0.0},
            },
            {
                "id": 3,
                "name": "Món Trung Bình",
                "criteria_scores": {
                    "price": 50.0,
                    "preference": 50.0,
                    "prep_time": 50.0,
                },
            },
        ]
        calculated = calculate_wsm(candidates, self.weights)

        # Món 1: 0.4*100 + 0.35*100 + 0.25*100 = 100.0
        self.assertEqual(calculated[0]["total_score"], 100.0)
        # Món 2: 0.0
        self.assertEqual(calculated[1]["total_score"], 0.0)
        # Món 3: 50.0
        self.assertEqual(calculated[2]["total_score"], 50.0)

    def test_wsm_score_candidates_with_equal_scores(self) -> None:
        """Kiểm tra hai phương án có điểm tổng kết giống nhau."""
        candidates = [
            {
                "id": 1,
                "name": "Món A",
                # 0.4*50 (20) + 0.35*60 (21) + 0.25*36 (9) = 50.0
                "criteria_scores": {
                    "price": 50.0,
                    "preference": 60.0,
                    "prep_time": 36.0,
                },
            },
            {
                "id": 2,
                "name": "Món B",
                # 0.4*75 (30) + 0.35*20 (7) + 0.25*52 (13) = 50.0
                "criteria_scores": {
                    "price": 75.0,
                    "preference": 20.0,
                    "prep_time": 52.0,
                },
            },
        ]
        calculated = calculate_wsm(candidates, self.weights)
        self.assertEqual(calculated[0]["total_score"], 50.0)
        self.assertEqual(calculated[1]["total_score"], 50.0)

    def test_wsm_score_missing_criterion_data_handling(self) -> None:
        """Kiểm tra tiêu chí có điểm normalized_score là None: không đóng góp vào tổng (contribution = 0.0)."""
        candidates = [
            {
                "id": 1,
                "name": "Món Thiếu Prep Time",
                "criteria_scores": {
                    "price": 80.0,
                    "preference": 100.0,
                    "prep_time": None,
                },
            }
        ]
        calculated = calculate_wsm(candidates, self.weights)
        item = calculated[0]

        # prep_time có normalized_score=None -> contribution=0.0
        self.assertIsNone(item["criteria_details"]["prep_time"]["normalized_score"])
        self.assertEqual(item["criteria_details"]["prep_time"]["contribution"], 0.0)

        # total_score = 0.4*80 (32) + 0.35*100 (35) + 0 = 67.0
        self.assertEqual(item["total_score"], 67.0)

    def test_wsm_food_specific_contract_functions(self) -> None:
        """Kiểm tra các hàm tính điểm tiêu chí con đặc thù của Food theo API Contract."""
        # 1. Price Score: 100 * (1 - price / budget_max)
        # 30k / 50k -> 100 * (1 - 0.6) = 40.0
        self.assertAlmostEqual(calculate_price_score(30000, 50000), 40.0)
        # Giá vượt ngân sách -> 0.0
        self.assertEqual(calculate_price_score(60000, 50000), 0.0)
        # Ngân sách <= 0 -> 0.0
        self.assertEqual(calculate_price_score(30000, 0), 0.0)

        # 2. Preference Score
        # Khớp 1 / 2 tag -> 50.0
        self.assertAlmostEqual(calculate_preference_score(["bò"], ["bò", "cay"]), 50.0)
        # Không chọn tag -> điểm trung tính 50.0
        self.assertAlmostEqual(calculate_preference_score(["bò"], None), 50.0)

        # 3. Prep Time Score
        # 15 phút / 30 phút -> 100 * (1 - 0.5) = 50.0
        self.assertAlmostEqual(calculate_prep_time_score(15, 30), 50.0)
        # Không giới hạn thời gian -> điểm trung tính 50.0
        self.assertAlmostEqual(calculate_prep_time_score(15, None), 50.0)
        # Thời gian vượt quá giới hạn -> 0.0
        self.assertEqual(calculate_prep_time_score(45, 30), 0.0)

        # 4. calculate_food_wsm tổng hợp
        result = calculate_food_wsm(
            price=30000,
            prep_time=15,
            food_tags=["bò"],
            budget_max=50000,
            max_prep_time=30,
            preferred_tags=["bò", "cay"],
        )
        # price_score=40.0 (w=0.4 -> 16), pref=50.0 (w=0.35 -> 17.5), prep=50.0 (w=0.25 -> 12.5)
        # Total = 16 + 17.5 + 12.5 = 46.0
        self.assertAlmostEqual(result.score, 46.0)
        self.assertEqual(result.rounded_score, 46.0)
        self.assertEqual(result.criteria_scores.price, 40.0)


# ==============================================================================
# 5. RANKING & TIE-BREAK UNIT TESTS
# ==============================================================================


class TestDecisionEngineRankingAndTieBreak(unittest.TestCase):
    """Kiểm tra thứ hạng phương án (Ranking) và quy tắc xử lý hòa điểm (Tie-break)."""

    def test_ranking_descending_by_total_score(self) -> None:
        """Sắp xếp phương án theo điểm giảm dần; phương án điểm cao nhất đứng hạng 1."""
        candidates = [
            {"id": 1, "name": "Món Điểm Thấp", "score": 30.0, "price": 40000},
            {"id": 2, "name": "Món Điểm Cao", "score": 85.5, "price": 40000},
            {"id": 3, "name": "Món Điểm Vừa", "score": 60.0, "price": 40000},
        ]
        ranked = rank_candidates(candidates)

        self.assertEqual(
            [r["name"] for r in ranked],
            ["Món Điểm Cao", "Món Điểm Vừa", "Món Điểm Thấp"],
        )
        self.assertEqual([r["rank"] for r in ranked], [1, 2, 3])
        self.assertEqual(ranked[0]["rank"], 1)

    def test_tie_break_level_1_lower_cost_priority(self) -> None:
        """Tie-break cấp 1: Hai phương án bằng điểm -> ưu tiên chi phí thấp hơn đứng trước."""
        candidates = [
            {"id": 1, "name": "Phở Gà Đắt", "price": 60000, "score": 70.0},
            {"id": 2, "name": "Bún Riêu Rẻ", "price": 45000, "score": 70.0},
        ]
        ranked = rank_candidates(candidates)

        # Bún Riêu Rẻ (45k) rẻ hơn Phở Gà Đắt (60k) -> Bún Riêu rank 1
        self.assertEqual(ranked[0]["name"], "Bún Riêu Rẻ")
        self.assertEqual(ranked[0]["rank"], 1)
        self.assertEqual(ranked[1]["name"], "Phở Gà Đắt")
        self.assertEqual(ranked[1]["rank"], 2)

    def test_tie_break_missing_cost_sentinel(self) -> None:
        """Ứng viên có giá/chi phí rõ ràng ưu tiên xếp trước ứng viên thiếu thông tin chi phí."""
        candidates = [
            {"id": 1, "name": "Món Không Rõ Giá", "price": None, "score": 70.0},
            {"id": 2, "name": "Món Có Giá", "price": 50000, "score": 70.0},
        ]
        ranked = rank_candidates(candidates)
        self.assertEqual(ranked[0]["name"], "Món Có Giá")
        self.assertEqual(ranked[1]["name"], "Món Không Rõ Giá")

    def test_tie_break_level_2_name_alphabetical(self) -> None:
        """Tie-break cấp 2: Cùng điểm, cùng chi phí -> sắp xếp theo tên tăng dần A-Z (không phân biệt hoa thường)."""
        candidates = [
            {"id": 1, "name": "Phở Bò", "price": 50000, "score": 70.0},
            {"id": 2, "name": "Bánh Cuốn", "price": 50000, "score": 70.0},
            {"id": 3, "name": "Cơm Sườn", "price": 50000, "score": 70.0},
        ]
        ranked = rank_candidates(candidates)

        # "bánh cuốn" (B) -> "cơm sườn" (C) -> "phở bò" (P)
        self.assertEqual(
            [r["name"] for r in ranked], ["Bánh Cuốn", "Cơm Sườn", "Phở Bò"]
        )
        self.assertEqual([r["rank"] for r in ranked], [1, 2, 3])

    def test_tie_break_level_3_id_ascending(self) -> None:
        """Tie-break cấp 3: Cùng điểm, cùng chi phí, cùng tên -> sắp xếp theo ID tăng dần."""
        candidates = [
            {"id": 205, "name": "Bún Chả", "price": 40000, "score": 60.0},
            {"id": 101, "name": "Bún Chả", "price": 40000, "score": 60.0},
            {"id": 150, "name": "Bún Chả", "price": 40000, "score": 60.0},
        ]
        ranked = rank_candidates(candidates)

        # 101 < 150 < 205
        self.assertEqual([r["id"] for r in ranked], [101, 150, 205])
        self.assertEqual([r["rank"] for r in ranked], [1, 2, 3])

    def test_tie_break_stable_identical_candidates(self) -> None:
        """Đảm bảo kết quả ổn định khi các phương án giống hệt nhau mọi trường (stable sort)."""
        candidates = [
            {
                "id": 1,
                "name": "Trà Sữa",
                "price": 30000,
                "score": 50.0,
                "tag": "item_1",
            },
            {
                "id": 1,
                "name": "Trà Sữa",
                "price": 30000,
                "score": 50.0,
                "tag": "item_2",
            },
            {
                "id": 1,
                "name": "Trà Sữa",
                "price": 30000,
                "score": 50.0,
                "tag": "item_3",
            },
        ]
        ranked = rank_candidates(candidates)

        # Giữ nguyên thứ tự ban đầu
        self.assertEqual([r["tag"] for r in ranked], ["item_1", "item_2", "item_3"])

    def test_ranking_limit_parameter(self) -> None:
        """Tham số limit chỉ trả về đúng Top N phương án điểm cao nhất."""
        candidates = [
            {"id": i, "name": f"Món {i}", "price": 30000, "score": float(i * 10)}
            for i in range(1, 6)
        ]
        ranked = rank_candidates(candidates, limit=3)

        self.assertEqual(len(ranked), 3)
        self.assertEqual([r["id"] for r in ranked], [5, 4, 3])
        self.assertEqual([r["rank"] for r in ranked], [1, 2, 3])

    def test_ranking_does_not_mutate_original_dict(self) -> None:
        """rank_candidates không làm thay đổi hay chèn trường rank vào dict gốc."""
        original = {"id": 10, "name": "Món X", "price": 20000, "score": 50.0}
        rank_candidates([original])
        self.assertNotIn("rank", original)


# ==============================================================================
# 6. EXPLANATION UNIT TESTS
# ==============================================================================


class TestDecisionEngineExplanation(unittest.TestCase):
    """Kiểm tra kết quả giải thích (Explanation: total_score, rank, normalized_score, weight, contribution, lý do loại)."""

    def setUp(self) -> None:
        self.criteria = [
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

    def test_explanation_valid_candidates_contain_all_required_fields(self) -> None:
        """Phương án hợp lệ phải có đầy đủ total_score, rank, normalized_score, weight, contribution."""
        candidates = [
            {
                "id": 1,
                "name": "Món A",
                "price": 30000,
                "preference": 80,
                "prep_time": 15,
            },
            {
                "id": 2,
                "name": "Món B",
                "price": 40000,
                "preference": 60,
                "prep_time": 20,
            },
        ]
        result = evaluate_decision(
            candidates=candidates,
            criteria=self.criteria,
            domain="food",
            budget_max=50000,
        )

        self.assertTrue(result["has_valid_candidates"])
        self.assertEqual(len(result["valid_candidates"]), 2)

        for cand in result["valid_candidates"]:
            # 1. Có total_score
            self.assertIn("total_score", cand)
            self.assertIsInstance(cand["total_score"], float)

            # 2. Có rank
            self.assertIn("rank", cand)
            self.assertIsInstance(cand["rank"], int)
            self.assertGreaterEqual(cand["rank"], 1)

            # 3. Có criteria_details
            self.assertIn("criteria_details", cand)
            details = cand["criteria_details"]

            for field_name in ("price", "preference", "prep_time"):
                self.assertIn(field_name, details)
                info = details[field_name]

                # normalized_score
                self.assertIn("normalized_score", info)
                self.assertIsInstance(info["normalized_score"], float)

                # weight
                self.assertIn("weight", info)
                self.assertIsInstance(info["weight"], float)

                # contribution
                self.assertIn("contribution", info)
                self.assertIsInstance(info["contribution"], float)

    def test_explanation_matches_actual_scoring_data(self) -> None:
        """Kiểm tra dữ liệu Explanation khớp chuẩn xác với kết quả Scoring thực tế."""
        candidates = [
            {
                "id": 1,
                "name": "Món Chuẩn",
                "price": 30000,
                "preference": 100,
                "prep_time": 10,
            },
            {
                "id": 2,
                "name": "Món Kém",
                "price": 50000,
                "preference": 50,
                "prep_time": 20,
            },
        ]
        result = evaluate_decision(
            candidates=candidates,
            criteria=self.criteria,
            domain="food",
            budget_max=50000,
        )

        top_cand = result["valid_candidates"][0]
        details = top_cand["criteria_details"]

        # Kiểm tra từng tiêu chí: contribution = round(weight * normalized_score, 6)
        for item in details.values():
            norm = item["normalized_score"]
            w = item["weight"]
            expected_contrib = round(w * norm, 6)
            self.assertAlmostEqual(item["contribution"], expected_contrib, places=6)

        # Kiểm tra total_score = round(sum(contributions), 2)
        sum_contrib = sum(d["contribution"] for d in details.values())
        self.assertEqual(top_cand["total_score"], round(sum_contrib, 2))
        self.assertEqual(top_cand["rank"], 1)

    def test_explanation_excluded_candidate_details(self) -> None:
        """Phương án bị loại phải có đầy đủ id, name, status, is_excluded và lý do bị loại."""
        candidates = [
            {
                "id": 99,
                "name": "Món Quá Đắt",
                "price": 100000,
                "meal_type": "lunch",
                "prep_time": 15,
            },
        ]
        result = evaluate_decision(
            candidates=candidates,
            criteria=self.criteria,
            domain="food",
            budget_max=50000,
        )

        self.assertFalse(result["has_valid_candidates"])
        self.assertEqual(len(result["excluded_candidates"]), 1)
        exc = result["excluded_candidates"][0]

        self.assertEqual(exc["id"], 99)
        self.assertEqual(exc["name"], "Món Quá Đắt")
        self.assertEqual(exc["status"], "excluded")
        self.assertTrue(exc["is_excluded"])
        self.assertIn("vượt quá ngân sách", exc["exclusion_reason"].lower())
        self.assertIn("100,000", exc["exclusion_reason"])
        self.assertTrue(len(exc["exclusion_reasons"]) > 0)


# ==============================================================================
# 7. END-TO-END PIPELINE & SERVICE INTEGRATION
# ==============================================================================


class TestDecisionEnginePipelineIntegration(unittest.TestCase):
    """Kiểm tra toàn bộ luồng tích hợp Pipeline và Response Model của Decision Engine."""

    def setUp(self) -> None:
        self.criteria = [
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

    def test_evaluate_helper_returns_valid_candidates_list(self) -> None:
        """Hàm evaluate() trả về trực tiếp danh sách valid_candidates đã xếp hạng."""
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
                "price": 40000,
                "preference": 80,
                "prep_time": 15,
            },
        ]
        ranked = evaluate(candidates, self.criteria, domain="food", budget_max=50000)
        self.assertEqual(len(ranked), 2)
        # Món X (30k) rẻ hơn Món Y (40k) -> Món X rank 1
        self.assertEqual(ranked[0]["name"], "Món X")
        self.assertEqual(ranked[0]["rank"], 1)

    def test_pydantic_decision_response_serialization(self) -> None:
        """Đảm bảo kết quả từ Engine tương thích hoàn toàn với schema DecisionResponse."""
        cand_data = {
            "id": 1,
            "food_id": 1,
            "name": "Phở Bò",
            "price": 45000,
            "meal_type": "lunch",
            "prep_time": 15,
            "score": 85.5,
            "total_score": 85.5,
            "rank": 1,
            "criteria_scores": CriteriaScores(
                price=80.0, preference=90.0, prep_time=85.0
            ),
            "criteria_details": {
                "price": CriterionDetail(
                    normalized_score=80.0, weight=0.4, contribution=32.0
                ),
                "preference": CriterionDetail(
                    normalized_score=90.0, weight=0.35, contribution=31.5
                ),
                "prep_time": CriterionDetail(
                    normalized_score=85.0, weight=0.25, contribution=21.25
                ),
            },
            "reasons": ["Giá hợp lý trong ngân sách", "Thời gian làm nhanh"],
        }
        item_response = RecommendedFoodResponse(**cand_data)
        self.assertEqual(item_response.food_id, 1)
        self.assertEqual(item_response.total_score, 85.5)
        self.assertEqual(item_response.rank, 1)

        excluded_data = {
            "id": 2,
            "name": "Lẩu Thái",
            "status": "excluded",
            "is_excluded": True,
            "exclusion_reason": "Vượt ngân sách",
            "exclusion_reasons": ["Vượt ngân sách"],
        }
        exc_response = ExcludedOptionResponse(**excluded_data)
        self.assertEqual(exc_response.id, 2)

        response = DecisionResponse(
            success=True,
            message="Đánh giá thành công.",
            has_valid_candidates=True,
            items=[item_response],
            excluded_items=[exc_response],
            total=1,
            total_excluded=1,
            limit=5,
            applied_filters=AppliedFilters(budget_max=50000),
        )
        self.assertTrue(response.success)
        self.assertEqual(len(response.items), 1)
        self.assertEqual(len(response.excluded_items), 1)


if __name__ == "__main__":
    unittest.main()
