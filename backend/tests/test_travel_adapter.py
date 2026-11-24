"""Unit and integration tests cho Travel Adapter (Module Travel -> Decision Engine)."""

import sys
import unittest
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.modules.decision.engine.pipeline import evaluate_decision
from app.modules.decision.models import DecisionCriterion
from app.modules.travel.adapter import (
    adapt_travel_candidate,
    adapt_travel_candidates,
    adapt_travel_criteria,
)
from app.modules.travel.models import TravelPlace, TravelRegion


class TestTravelCandidateAdapter(unittest.TestCase):
    def test_adapt_travel_place_orm(self) -> None:
        """Kiểm tra chuyển đổi TravelPlace ORM đầy đủ thuộc tính sang dict chuẩn."""
        place = TravelPlace(
            id=1,
            name="Vịnh Hạ Long",
            province_city="Quảng Ninh",
            region=TravelRegion.BAC,
            estimated_cost=650000,
            estimated_duration=Decimal("6.5"),
            activity_type="Khám phá thiên nhiên",
            highlights="Thăm hang Sửng Sốt, Chèo thuyền kayak, Ngắm hoàng hôn trên vịnh",
            description="Di sản thiên nhiên thế giới với hàng nghìn đảo đá vôi.",
            image_url="https://example.com/halong.jpg",
            rating=Decimal("4.8"),
            is_active=True,
        )

        adapted = adapt_travel_candidate(place)

        self.assertEqual(adapted["id"], 1)
        self.assertEqual(adapted["destination_id"], 1)
        self.assertEqual(adapted["name"], "Vịnh Hạ Long")
        self.assertEqual(adapted["province_city"], "Quảng Ninh")
        self.assertEqual(adapted["region"], "Bắc")
        self.assertEqual(adapted["estimated_cost"], 650000)
        self.assertEqual(adapted["estimated_duration"], 6.5)
        self.assertEqual(adapted["activities"], 3.0)
        self.assertEqual(adapted["activity_type"], "Khám phá thiên nhiên")
        self.assertEqual(
            adapted["highlights"],
            ["Thăm hang Sửng Sốt", "Chèo thuyền kayak", "Ngắm hoàng hôn trên vịnh"],
        )
        self.assertEqual(adapted["rating"], 4.8)
        self.assertIs(adapted["item"], place)

    def test_adapt_dict_candidate_with_aliases(self) -> None:
        """Dict có thể dùng alias 'cost', 'duration' và string number."""
        raw_dict = {
            "destination_id": 2,
            "name": "Phố cổ Hội An",
            "province_city": "Quảng Nam",
            "region": "Trung",
            "cost": "450000",
            "duration": "8.0",
            "activities": 4,
            "activity_type": "Văn hóa lịch sử",
            "highlights": ["Thả đèn hoa đăng", "Đi thuyền sông Hoài", "Chùa Cầu", "Cao lầu"],
        }

        adapted = adapt_travel_candidate(raw_dict)

        self.assertEqual(adapted["id"], 2)
        self.assertEqual(adapted["destination_id"], 2)
        self.assertEqual(adapted["name"], "Phố cổ Hội An")
        self.assertEqual(adapted["estimated_cost"], 450000)
        self.assertEqual(adapted["estimated_duration"], 8.0)
        self.assertEqual(adapted["activities"], 4.0)
        self.assertEqual(adapted["region"], "Trung")

    def test_adapt_candidate_with_missing_fields_graceful(self) -> None:
        """Ứng viên thiếu trường hoặc sai kiểu dữ liệu được gán giá trị an toàn, không crash."""
        raw = SimpleNamespace(name="Địa điểm tối giản")
        adapted = adapt_travel_candidate(raw)

        self.assertEqual(adapted["id"], 0)
        self.assertEqual(adapted["name"], "Địa điểm tối giản")
        self.assertEqual(adapted["estimated_cost"], 0)
        self.assertEqual(adapted["estimated_duration"], 0.0)
        self.assertEqual(adapted["activities"], 0.0)
        self.assertEqual(adapted["highlights"], [])
        self.assertIsNone(adapted["rating"])

    def test_adapt_candidates_batch(self) -> None:
        """Chuyển đổi danh sách nhiều ứng viên và xử lý danh sách rỗng."""
        self.assertEqual(adapt_travel_candidates([]), [])

        items = [
            {"id": 1, "name": "A", "estimated_cost": 100, "estimated_duration": 2.0},
            {"id": 2, "name": "B", "estimated_cost": 200, "estimated_duration": 4.0},
        ]
        results = adapt_travel_candidates(items)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["name"], "A")
        self.assertEqual(results[1]["name"], "B")


class TestTravelCriteriaAdapter(unittest.TestCase):
    def test_default_travel_criteria(self) -> None:
        """Khi criteria là None hoặc rỗng, trả về tiêu chí Travel mặc định (tổng weight = 1.0)."""
        criteria = adapt_travel_criteria()

        self.assertEqual(len(criteria), 3)
        field_names = [c["field_name"] for c in criteria]
        self.assertIn("estimated_cost", field_names)
        self.assertIn("estimated_duration", field_names)
        self.assertIn("activities", field_names)

        total_weight = sum(c["weight"] for c in criteria)
        self.assertAlmostEqual(total_weight, 1.0, places=4)

    def test_adapt_criteria_from_db_models(self) -> None:
        """Chuyển đổi các bản ghi DecisionCriterion từ DB sang cấu trúc Engine."""
        db_criteria = [
            DecisionCriterion(
                domain="travel",
                name="cost",
                direction="min",
                weight=Decimal("0.4000"),
            ),
            DecisionCriterion(
                domain="travel",
                name="duration",
                direction="min",
                weight=Decimal("0.3000"),
            ),
            DecisionCriterion(
                domain="travel",
                name="activities",
                direction="max",
                weight=Decimal("0.3000"),
            ),
        ]

        adapted = adapt_travel_criteria(db_criteria)

        self.assertEqual(len(adapted), 3)
        self.assertEqual(adapted[0]["field_name"], "estimated_cost")
        self.assertEqual(adapted[1]["field_name"], "estimated_duration")
        self.assertEqual(adapted[2]["field_name"], "activities")
        self.assertEqual(adapted[0]["direction"], "min")
        self.assertEqual(adapted[2]["direction"], "max")

    def test_adapt_criteria_with_custom_weights(self) -> None:
        """Ghi đè trọng số tùy chỉnh và chuẩn hóa key."""
        custom = {"cost": 0.50, "duration": 0.25, "activities": 0.25}
        adapted = adapt_travel_criteria(custom_weights=custom)

        weights = {c["field_name"]: c["weight"] for c in adapted}
        self.assertEqual(
            weights,
            {"estimated_cost": 0.50, "estimated_duration": 0.25, "activities": 0.25},
        )

    def test_adapt_criteria_invalid_custom_weights_raises(self) -> None:
        """Tổng trọng số khác 1.0 hoặc có trọng số âm sẽ raise ValueError."""
        with self.assertRaises(ValueError):
            adapt_travel_criteria(custom_weights={"cost": 0.6, "duration": 0.6, "activities": 0.1})

        with self.assertRaises(ValueError):
            adapt_travel_criteria(custom_weights={"cost": -0.2, "duration": 0.6, "activities": 0.6})


class TestTravelDecisionEngineIntegration(unittest.TestCase):
    def test_end_to_end_travel_decision_pipeline(self) -> None:
        """Toàn bộ luồng: TravelPlaces -> Adapter -> Decision Engine -> Ranked Results."""
        places = [
            TravelPlace(
                id=1,
                name="Địa điểm A (Giá rẻ, nhiều hoạt động)",
                province_city="Quảng Nam",
                region=TravelRegion.TRUNG,
                estimated_cost=300000,
                estimated_duration=Decimal("4.0"),
                activity_type="Văn hóa lịch sử",
                highlights="H1, H2, H3, H4, H5",  # 5 hoạt động
                is_active=True,
            ),
            TravelPlace(
                id=2,
                name="Địa điểm B (Chi phí cao, ít hoạt động)",
                province_city="Đà Nẵng",
                region=TravelRegion.TRUNG,
                estimated_cost=900000,
                estimated_duration=Decimal("8.0"),
                activity_type="Nghỉ dưỡng biển",
                highlights="H1, H2",  # 2 hoạt động
                is_active=True,
            ),
        ]

        adapted_candidates = adapt_travel_candidates(places)
        adapted_criteria = adapt_travel_criteria()

        result = evaluate_decision(
            candidates=adapted_candidates,
            criteria=adapted_criteria,
            domain="travel",
        )

        self.assertTrue(result["success"])
        self.assertTrue(result["has_valid_candidates"])
        self.assertEqual(result["total_valid"], 2)

        valid = result["valid_candidates"]
        self.assertEqual(len(valid), 2)
        # Địa điểm A rẻ hơn, thời lượng ngắn hơn, nhiều hoạt động hơn -> điểm cao hơn -> rank 1
        self.assertEqual(valid[0]["name"], "Địa điểm A (Giá rẻ, nhiều hoạt động)")
        self.assertEqual(valid[0]["rank"], 1)
        self.assertGreater(valid[0]["score"], valid[1]["score"])

        # Kiểm tra criteria_scores có đủ 3 tiêu chí
        scores = valid[0]["criteria_scores"]
        self.assertIn("estimated_cost", scores)
        self.assertIn("estimated_duration", scores)
        self.assertIn("activities", scores)


if __name__ == "__main__":
    unittest.main()
