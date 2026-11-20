"""Kiểm thử API Endpoint POST /api/v1/decisions/recommend.

Kiểm tra:
1. API trả về đầy đủ total_score, rank, criteria_details (weight, normalized_score, contribution) khi scoring thành công.
2. API trả về excluded_items kèm id, name, status, exclusion_reason khi có phương án bị loại.
3. API trả về has_valid_candidates=False và thông báo khi không có phương án nào thỏa mãn.
4. Validation lỗi khi input không hợp lệ (ví dụ budget_max <= 0).
"""

"""Kiểm thử API Endpoint POST /api/v1/decisions/recommend.

Kiểm tra:
1. Endpoint trả về đầy đủ total_score, rank, criteria_details (weight, normalized_score, contribution) khi scoring thành công.
2. Endpoint trả về excluded_items kèm id, name, status, exclusion_reason khi có phương án bị loại.
3. Endpoint trả về has_valid_candidates=False và thông báo khi không có phương án nào thỏa mãn.
4. Validation schema khi input không hợp lệ (ví dụ budget_max <= 0).
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.modules.decision.router import recommend_decisions
from app.modules.decision.schema import DecisionRecommendRequest
from pydantic import ValidationError


class TestDecisionRecommendAPI(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_db = MagicMock()
        # Mock DB trả về empty để kích hoạt fallback sang candidates mẫu
        self.mock_db.query.return_value.filter.return_value.all.return_value = []
        self.mock_db.query.return_value.options.return_value.filter.return_value.all.return_value = []

    def test_api_recommend_success(self) -> None:
        """API trả về đầy đủ total_score, rank, contribution từng tiêu chí."""
        payload = DecisionRecommendRequest(
            budget_max=50000,
            meal_type="lunch",
            max_prep_time=30,
            preferred_tags=["vegetarian"],
            limit=5,
        )
        response = recommend_decisions(payload=payload, db=self.mock_db)

        self.assertTrue(response.success)
        self.assertTrue(response.has_valid_candidates)
        self.assertGreater(response.total, 0)

        first_item = response.items[0]
        self.assertTrue(first_item.food_id > 0)
        self.assertTrue(len(first_item.name) > 0)
        self.assertGreater(first_item.total_score, 0.0)
        self.assertEqual(first_item.rank, 1)

        # Kiểm tra chi tiết tiêu chí
        details = first_item.criteria_details
        self.assertIn("price", details)
        self.assertGreater(details["price"].weight, 0.0)
        self.assertIsNotNone(details["price"].normalized_score)
        self.assertGreaterEqual(details["price"].contribution, 0.0)

    def test_api_recommend_with_exclusions(self) -> None:
        """API trả về danh sách excluded_items kèm lý do cụ thể khi có phương án bị loại."""
        payload = DecisionRecommendRequest(
            budget_max=25000,  # 25k -> Món A (30k) và B (40k) bị loại
            limit=5,
        )
        response = recommend_decisions(payload=payload, db=self.mock_db)

        self.assertTrue(response.success)
        self.assertGreater(response.total_excluded, 0)
        self.assertGreater(len(response.excluded_items), 0)

        # Kiểm tra phương án bị loại
        for exc in response.excluded_items:
            self.assertTrue(exc.id > 0)
            self.assertTrue(len(exc.name) > 0)
            self.assertEqual(exc.status, "excluded")
            self.assertTrue(exc.is_excluded)
            self.assertIn("vượt quá ngân sách", exc.exclusion_reason.lower())

    def test_api_recommend_all_excluded(self) -> None:
        """Khi ngân sách quá thấp khiến tất cả bị loại: has_valid_candidates=False, không có items."""
        payload = DecisionRecommendRequest(
            budget_max=5000,  # Không có món nào <= 5k
            limit=5,
        )
        response = recommend_decisions(payload=payload, db=self.mock_db)

        self.assertFalse(response.has_valid_candidates)
        self.assertEqual(response.total, 0)
        self.assertEqual(len(response.items), 0)
        self.assertGreater(response.total_excluded, 0)
        self.assertIn("không có phương án hợp lệ", response.message.lower())

    def test_api_validation_error_invalid_budget(self) -> None:
        """Payload không hợp lệ (budget_max <= 0) bị từ chối với ValidationError."""
        with self.assertRaises(ValidationError):
            DecisionRecommendRequest(
                budget_max=0,  # gt=0 bị vi phạm
            )


if __name__ == "__main__":
    unittest.main()
