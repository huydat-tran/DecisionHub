"""Tests cho endpoint và service Travel Recommendation."""

import sys
from decimal import Decimal
from pathlib import Path
import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import Base, get_db
from app.main import app
from app.modules.travel.models import TravelPlace, TravelRegion
from app.modules.travel.schemas import TravelRecommendRequest
from app.modules.travel.services import recommend_travel


class TestTravelRecommendation(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=cls.engine
        )
        Base.metadata.create_all(bind=cls.engine)

        def override_get_db():
            db = cls.TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls) -> None:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=cls.engine)

    def setUp(self) -> None:
        self.db = self.TestingSessionLocal()
        # Xóa dữ liệu cũ
        self.db.query(TravelPlace).delete()
        self.db.commit()

        # Seed 4 địa điểm phong phú
        self.places = [
            TravelPlace(
                id=1,
                name="Phố cổ Hội An",
                province_city="Quảng Nam",
                region=TravelRegion.TRUNG,
                estimated_cost=500000,
                estimated_duration=Decimal("8.0"),
                activity_type="Văn hóa lịch sử",
                highlights="Thả đèn hoa đăng trên sông Hoài, Thưởng thức cao lầu, Check-in Chùa Cầu",
                description="Đô thị cổ được UNESCO công nhận là Di sản Thế giới.",
                is_active=True,
            ),
            TravelPlace(
                id=2,
                name="Vịnh Hạ Long",
                province_city="Quảng Ninh",
                region=TravelRegion.BAC,
                estimated_cost=650000,
                estimated_duration=Decimal("6.5"),
                activity_type="Khám phá thiên nhiên",
                highlights="Thăm hang Sửng Sốt, Chèo thuyền kayak, Ngắm hoàng hôn trên vịnh",
                description="Di sản thiên nhiên thế giới.",
                is_active=True,
            ),
            TravelPlace(
                id=3,
                name="Quần thể Tràng An",
                province_city="Ninh Bình",
                region=TravelRegion.BAC,
                estimated_cost=400000,
                estimated_duration=Decimal("5.0"),
                activity_type="Khám phá thiên nhiên",
                highlights="Đi thuyền nan ngắm hang động, Viếng đền Trình, Leo núi ngắm thung lũng",
                description="Di sản thế giới kép.",
                is_active=True,
            ),
            TravelPlace(
                id=4,
                name="Bà Nà Hills",
                province_city="Đà Nẵng",
                region=TravelRegion.TRUNG,
                estimated_cost=950000,
                estimated_duration=Decimal("7.0"),
                activity_type="Vui chơi giải trí",
                highlights="Cầu Vàng, Cáp treo Bà Nà, Làng Pháp",
                description="Khu du lịch trên đỉnh núi Chúa.",
                is_active=True,
            ),
        ]
        self.db.add_all(self.places)
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()

    def test_recommend_travel_all_places_ranked_wsm(self) -> None:
        """Endpoint /api/v1/travel/recommend trả về danh sách được xếp hạng WSM."""
        response = self.client.post("/api/v1/travel/recommend", json={"limit": 5})
        self.assertEqual(response.status_code, 200)

        body = response.json()
        self.assertTrue(body["success"])
        self.assertIn("data", body)
        data = body["data"]

        items = data["items"]
        self.assertEqual(len(items), 4)

        # Thứ hạng giảm dần theo score
        scores = [item["score"] for item in items]
        self.assertEqual(scores, sorted(scores, reverse=True))

        # Kiểm tra rank đánh số 1, 2, 3, 4
        ranks = [item["rank"] for item in items]
        self.assertEqual(ranks, [1, 2, 3, 4])

        # Kiểm tra criteria_scores có đủ estimated_cost, estimated_duration, activities
        first = items[0]
        self.assertIn("estimated_cost", first["criteria_scores"])
        self.assertIn("estimated_duration", first["criteria_scores"])
        self.assertIn("activities", first["criteria_scores"])

        # Kiểm tra reasons (1-3 lý do)
        self.assertGreaterEqual(len(first["reasons"]), 1)
        self.assertLessEqual(len(first["reasons"]), 3)

    def test_filter_by_budget_max(self) -> None:
        """Lọc ngân sách tối đa loại bỏ địa điểm có chi phí vượt quá giới hạn."""
        response = self.client.post(
            "/api/v1/travel/recommend",
            json={"budget_max": 500000},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]

        items = data["items"]
        # Chỉ Hội An (500k) và Tràng An (400k) thỏa mãn
        self.assertEqual(len(items), 2)
        item_names = {item["name"] for item in items}
        self.assertEqual(item_names, {"Phố cổ Hội An", "Quần thể Tràng An"})

        # Hạ Long (650k) và Bà Nà (950k) bị loại
        self.assertEqual(data["total_excluded"], 2)

    def test_filter_by_max_duration(self) -> None:
        """Lọc thời lượng tối đa loại bỏ địa điểm có thời gian vượt giới hạn."""
        response = self.client.post(
            "/api/v1/travel/recommend",
            json={"max_duration": 6.5},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]

        items = data["items"]
        # Tràng An (5.0h) và Hạ Long (6.5h) thỏa mãn <= 6.5h
        self.assertEqual(len(items), 2)
        item_names = {item["name"] for item in items}
        self.assertEqual(item_names, {"Quần thể Tràng An", "Vịnh Hạ Long"})

    def test_combined_filters_budget_duration_region(self) -> None:
        """Kết hợp lọc ngân sách, thời lượng và khu vực."""
        response = self.client.post(
            "/api/v1/travel/recommend",
            json={
                "budget_max": 700000,
                "max_duration": 7.0,
                "region": "Bắc",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        items = data["items"]

        # Vịnh Hạ Long (Bắc, 650k, 6.5h) và Tràng An (Bắc, 400k, 5.0h)
        self.assertEqual(len(items), 2)
        for item in items:
            self.assertEqual(item["region"], "Bắc")
            self.assertLessEqual(item["estimated_cost"], 700000)
            self.assertLessEqual(item["estimated_duration"], 7.0)

    def test_preferred_activities_boosts_ranking(self) -> None:
        """Sở thích / hoạt động ưu tiên giúp địa điểm khớp nổi bật hơn."""
        # Ưu tiên hoạt động 'kayak'
        response = self.client.post(
            "/api/v1/travel/recommend",
            json={"preferred_activities": ["kayak"]},
        )
        self.assertEqual(response.status_code, 200)
        items = response.json()["data"]["items"]

        # Vịnh Hạ Long có chèo thuyền kayak nên hoạt động được khớp
        ha_long = next(item for item in items if item["name"] == "Vịnh Hạ Long")
        self.assertTrue(any("kayak" in r.lower() for r in ha_long["reasons"]))

    def test_no_valid_candidates_when_budget_too_low(self) -> None:
        """Khi không có địa điểm nào thỏa mãn, trả về danh sách rỗng và thông báo hướng dẫn."""
        response = self.client.post(
            "/api/v1/travel/recommend",
            json={"budget_max": 100000},  # Mọi địa điểm đều > 100k
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body["data"]["items"]), 0)
        self.assertEqual(body["data"]["total_excluded"], 4)
        self.assertIn("tăng ngân sách", body["message"])

    def test_validation_negative_budget_and_duration_rejected(self) -> None:
        """Số âm cho ngân sách hoặc thời lượng bị từ chối với mã lỗi 422."""
        res_budget = self.client.post(
            "/api/v1/travel/recommend",
            json={"budget_max": -50000},
        )
        self.assertEqual(res_budget.status_code, 422)

        res_dur = self.client.post(
            "/api/v1/travel/recommend",
            json={"max_duration": -2.0},
        )
        self.assertEqual(res_dur.status_code, 422)

    def test_decisions_router_alias(self) -> None:
        """Endpoint /api/v1/decisions/travel/recommend hoạt động đồng nhất."""
        response = self.client.post(
            "/api/v1/decisions/travel/recommend",
            json={"limit": 3},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(len(data["items"]), 3)


if __name__ == "__main__":
    unittest.main()
