"""Kiểm thử validation đầu vào cho POST /api/v1/decisions/recommend và format lỗi 422."""

from pathlib import Path
import sys
import unittest

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.modules.decision.schema import WeightsInput

ENDPOINT = "/api/v1/decisions/recommend"
STANDARD_ERROR_KEYS = {"success", "message", "data", "error_code", "errors", "path"}


class TestRecommendValidation(unittest.TestCase):
    """Kiểm tra validation weights, budget_max, meal_type và cấu trúc lỗi 422."""

    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def _assert_422_error(
        self,
        payload: dict,
        expected_field: str,
        expected_msg_substr: str | None = None,
    ) -> dict:
        response = self.client.post(ENDPOINT, json=payload)
        self.assertEqual(response.status_code, 422)
        body = response.json()
        self.assertEqual(set(body.keys()), STANDARD_ERROR_KEYS)
        self.assertFalse(body["success"])
        self.assertEqual(body["message"], "Dữ liệu đầu vào không hợp lệ")
        self.assertIsNone(body["data"])
        self.assertEqual(body["error_code"], "VALIDATION_ERROR")
        self.assertEqual(body["path"], ENDPOINT)
        self.assertIsInstance(body["errors"], list)
        self.assertTrue(body["errors"])

        matched = [err for err in body["errors"] if err.get("field") == expected_field]
        self.assertTrue(
            matched,
            f"Không thấy field {expected_field!r} trong errors: {body['errors']}",
        )
        if expected_msg_substr is not None:
            self.assertTrue(
                any(expected_msg_substr in str(err.get("message", "")) for err in matched),
                f"Message {matched!r} không chứa {expected_msg_substr!r}",
            )
        return body

    # ------------------------------------------------------------------
    # 1. Các trường hợp hợp lệ (HTTP 200)
    # ------------------------------------------------------------------

    def test_valid_request_without_weights_uses_default(self) -> None:
        response = self.client.post(ENDPOINT, json={"budget_max": 50000})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(
            body["scoring"]["weights"],
            {"price": 0.4, "preference": 0.35, "prep_time": 0.25},
        )

    def test_valid_custom_weights_and_float_precision(self) -> None:
        valid_weights_cases = [
            {"price": 0.4, "preference": 0.35, "prep_time": 0.25},
            {"price": 0.33, "preference": 0.33, "prep_time": 0.34},
            {"price": 0.1, "preference": 0.2, "prep_time": 0.7},
            {"price": 1.0, "preference": 0.0, "prep_time": 0.0},
        ]
        for weights in valid_weights_cases:
            with self.subTest(weights=weights):
                response = self.client.post(
                    ENDPOINT,
                    json={"budget_max": 50000, "weights": weights},
                )
                self.assertEqual(response.status_code, 200)
                returned_weights = response.json()["scoring"]["weights"]
                self.assertAlmostEqual(returned_weights["price"], weights["price"])
                self.assertAlmostEqual(
                    returned_weights["preference"], weights["preference"]
                )
                self.assertAlmostEqual(
                    returned_weights["prep_time"], weights["prep_time"]
                )

    def test_valid_meal_types(self) -> None:
        for meal_type in ("breakfast", "lunch", "dinner", "snack", None):
            with self.subTest(meal_type=meal_type):
                response = self.client.post(
                    ENDPOINT,
                    json={"budget_max": 50000, "meal_type": meal_type},
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["applied_filters"]["meal_type"], meal_type)

    # ------------------------------------------------------------------
    # 2. Kiểm tra weights không hợp lệ (HTTP 422)
    # ------------------------------------------------------------------

    def test_negative_weight_returns_422(self) -> None:
        self._assert_422_error(
            {
                "budget_max": 50000,
                "weights": {"price": -0.1, "preference": 0.6, "prep_time": 0.5},
            },
            expected_field="body.weights.price",
            expected_msg_substr="không được âm",
        )

    def test_weight_greater_than_one_returns_422(self) -> None:
        self._assert_422_error(
            {
                "budget_max": 50000,
                "weights": {"price": 1.2, "preference": 0.0, "prep_time": 0.0},
            },
            expected_field="body.weights.price",
            expected_msg_substr="không được vượt quá 1.0",
        )

    def test_weight_sum_invalid_returns_422(self) -> None:
        invalid_sums = [
            {"price": 0.3, "preference": 0.3, "prep_time": 0.3},
            {"price": 0.5, "preference": 0.4, "prep_time": 0.3},
            {"price": 0.0, "preference": 0.0, "prep_time": 0.0},
        ]
        for weights in invalid_sums:
            with self.subTest(weights=weights):
                self._assert_422_error(
                    {"budget_max": 50000, "weights": weights},
                    expected_field="body.weights",
                    expected_msg_substr="Tổng trọng số phải bằng 1.0",
                )

    def test_boolean_weight_returns_422(self) -> None:
        self._assert_422_error(
            {
                "budget_max": 50000,
                "weights": {"price": True, "preference": 0.0, "prep_time": 0.0},
            },
            expected_field="body.weights.price",
            expected_msg_substr="boolean",
        )

    def test_missing_or_extra_weight_field_returns_422(self) -> None:
        self._assert_422_error(
            {
                "budget_max": 50000,
                "weights": {"price": 0.5, "preference": 0.5},
            },
            expected_field="body.weights.prep_time",
        )
        self._assert_422_error(
            {
                "budget_max": 50000,
                "weights": {
                    "price": 0.4,
                    "preference": 0.35,
                    "prep_time": 0.25,
                    "extra": 0.0,
                },
            },
            expected_field="body.weights.extra",
        )

    def test_non_finite_weight_returns_422_and_schema_raises(self) -> None:
        for raw_val in ("nan", "inf", "-inf"):
            with self.subTest(raw_val=raw_val):
                self._assert_422_error(
                    {
                        "budget_max": 50000,
                        "weights": {"price": raw_val, "preference": 0.5, "prep_time": 0.5},
                    },
                    expected_field="body.weights.price",
                    expected_msg_substr="hữu hạn",
                )

        for float_val in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(float_val=float_val):
                with self.assertRaises(ValidationError):
                    WeightsInput(price=float_val, preference=0.5, prep_time=0.5)

    # ------------------------------------------------------------------
    # 3. Kiểm tra budget_max không hợp lệ (HTTP 422)
    # ------------------------------------------------------------------

    def test_invalid_budget_max_returns_422(self) -> None:
        cases = [
            (-10000, "lớn hơn 0"),
            (0, "lớn hơn 0"),
            (True, "số nguyên dương lớn hơn 0"),
            (50000.5, "số nguyên dương lớn hơn 0"),
            (None, "không được để trống"),
            ("abc", "số nguyên dương lớn hơn 0"),
        ]
        for bad_budget, msg_substr in cases:
            with self.subTest(budget_max=bad_budget):
                self._assert_422_error(
                    {"budget_max": bad_budget},
                    expected_field="body.budget_max",
                    expected_msg_substr=msg_substr,
                )

        self._assert_422_error({}, expected_field="body.budget_max")

    # ------------------------------------------------------------------
    # 4. Kiểm tra meal_type không hợp lệ (HTTP 422)
    # ------------------------------------------------------------------

    def test_invalid_meal_type_returns_422(self) -> None:
        for bad_meal in ("brunch", "", "   ", "LUNCH", 123):
            with self.subTest(meal_type=bad_meal):
                self._assert_422_error(
                    {"budget_max": 50000, "meal_type": bad_meal},
                    expected_field="body.meal_type",
                    expected_msg_substr="Loại bữa ăn (meal_type) không hợp lệ",
                )


if __name__ == "__main__":
    unittest.main()
