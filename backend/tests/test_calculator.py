"""Unit tests cho Bước 4 - WSM Calculator (kiểm tra weight, tính tổng Σ(w × s), dữ liệu thiếu)."""

from decimal import Decimal
from pathlib import Path
import sys
import unittest

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.modules.decision.engine.calculator import (
    calculate_wsm,
    validate_weights,
)


class TestValidateWeights(unittest.TestCase):
    """Kiểm tra validate_weights() với nhiều dạng đầu vào."""

    def test_valid_list_sums_to_one(self) -> None:
        """Tổng weight đúng bằng 1.0 → trả dict field_name: weight."""
        criteria = [
            {"name": "Giá", "weight": Decimal("0.4000")},
            {"name": "Mức phù hợp nhu cầu/khẩu vị", "weight": Decimal("0.3500")},
            {"name": "Thời gian chuẩn bị", "weight": Decimal("0.2500")},
        ]
        weights = validate_weights(criteria)
        self.assertAlmostEqual(weights["price"], 0.40)
        self.assertAlmostEqual(weights["preference"], 0.35)
        self.assertAlmostEqual(weights["prep_time"], 0.25)

    def test_valid_dict_sums_to_one(self) -> None:
        """Dict trực tiếp {field: weight} cũng được chấp nhận."""
        weights = validate_weights({"price": 0.5, "preference": 0.3, "prep_time": 0.2})
        self.assertAlmostEqual(weights["price"], 0.5)
        self.assertAlmostEqual(weights["preference"], 0.3)
        self.assertAlmostEqual(weights["prep_time"], 0.2)

    def test_total_weight_less_than_one_raises(self) -> None:
        """Tổng weight < 1.0 phải raise ValueError chứa '1.0'."""
        with self.assertRaises(ValueError) as ctx:
            validate_weights([
                {"name": "price", "weight": 0.4},
                {"name": "preference", "weight": 0.5},
            ])
        self.assertIn("1.0", str(ctx.exception))

    def test_total_weight_greater_than_one_raises(self) -> None:
        """Tổng weight > 1.0 phải raise ValueError chứa '1.0'."""
        with self.assertRaises(ValueError) as ctx:
            validate_weights({"price": 0.6, "preference": 0.5})
        self.assertIn("1.0", str(ctx.exception))

    def test_negative_weight_raises(self) -> None:
        """Weight âm phải raise ValueError chứa 'không được âm'."""
        with self.assertRaises(ValueError) as ctx:
            validate_weights([
                {"name": "price", "weight": -0.2},
                {"name": "preference", "weight": 1.2},
            ])
        self.assertIn("không được âm", str(ctx.exception))

    def test_none_weight_raises(self) -> None:
        """Weight None phải raise ValueError."""
        with self.assertRaises(ValueError):
            validate_weights([
                {"name": "price", "weight": None},
                {"name": "preference", "weight": 1.0},
            ])

    def test_bool_weight_raises(self) -> None:
        """Weight dạng bool (True) phải raise ValueError (bool không phải số hợp lệ)."""
        with self.assertRaises(ValueError):
            validate_weights([{"name": "price", "weight": True}])

    def test_invalid_string_weight_raises(self) -> None:
        """Weight chuỗi không chuyển đổi được phải raise ValueError."""
        with self.assertRaises(ValueError):
            validate_weights([
                {"name": "price", "weight": "khong_hop_le"},
                {"name": "prep_time", "weight": 1.0},
            ])

    def test_nan_weight_raises(self) -> None:
        """Weight NaN phải raise ValueError."""
        with self.assertRaises(ValueError):
            validate_weights({"price": float("nan"), "prep_time": 1.0})

    def test_empty_list_raises(self) -> None:
        """Danh sách rỗng phải raise ValueError."""
        with self.assertRaises(ValueError):
            validate_weights([])

    def test_empty_dict_raises(self) -> None:
        """Dict rỗng phải raise ValueError."""
        with self.assertRaises(ValueError):
            validate_weights({})


class TestCalculateWSM(unittest.TestCase):
    """Kiểm tra calculate_wsm() tính tổng Σ(w × s) đúng."""

    def setUp(self) -> None:
        self.criteria = [
            {"name": "Giá", "weight": 0.40},
            {"name": "Mức phù hợp nhu cầu/khẩu vị", "weight": 0.35},
            {"name": "Thời gian chuẩn bị", "weight": 0.25},
        ]

    def test_empty_candidates_returns_empty_list(self) -> None:
        """Danh sách rỗng → trả danh sách rỗng."""
        self.assertEqual(calculate_wsm([], self.criteria), [])

    def test_calculate_wsm_normal(self) -> None:
        """Tính đúng công thức Σ(w × s) và làm tròn 2 chữ số."""
        candidates = [
            {
                "id": 1,
                "name": "Món A",
                "criteria_scores": {"price": 40.0, "preference": 100.0, "prep_time": 50.0},
            },
            {
                "id": 2,
                "name": "Món B",
                "criteria_scores": {"price": 20.0, "preference": 50.0, "prep_time": 66.67},
            },
            {
                "id": 3,
                "name": "Món C",
                "criteria_scores": {"price": 60.0, "preference": 50.0, "prep_time": 33.33},
            },
        ]
        results = calculate_wsm(candidates, self.criteria)

        # Món A: 0.4*40 + 0.35*100 + 0.25*50 = 16.0 + 35.0 + 12.5 = 63.50
        self.assertEqual(results[0]["score"], 63.50)

        # Món B: 0.4*20 + 0.35*50 + 0.25*66.67 = 8.0 + 17.5 + 16.6675 ≈ 42.17
        self.assertEqual(results[1]["score"], 42.17)

        # Món C: 0.4*60 + 0.35*50 + 0.25*33.33 = 24.0 + 17.5 + 8.3325 ≈ 49.83
        self.assertEqual(results[2]["score"], 49.83)

    def test_missing_criterion_score_not_imputed(self) -> None:
        """Tiêu chí có normalized_score là None không đóng góp vào tổng."""
        candidates = [
            {
                "id": 1,
                "name": "Cơm tấm",
                "criteria_scores": {"price": 50.0, "preference": 50.0, "prep_time": None},
            }
        ]
        results = calculate_wsm(candidates, self.criteria)

        # prep_time None → không tự suy diễn
        # total = 0.40*50 + 0.35*50 = 20.0 + 17.5 = 37.50
        self.assertEqual(results[0]["score"], 37.50)
        self.assertIsNone(results[0]["criteria_scores"]["prep_time"])

    def test_does_not_mutate_input_dict(self) -> None:
        """calculate_wsm() không được sửa dict ứng viên gốc."""
        original = {
            "id": 1,
            "name": "Phở",
            "criteria_scores": {"price": 100.0, "preference": 100.0, "prep_time": 100.0},
        }
        calculate_wsm([original], self.criteria)
        self.assertNotIn("score", original)


if __name__ == "__main__":
    unittest.main()
