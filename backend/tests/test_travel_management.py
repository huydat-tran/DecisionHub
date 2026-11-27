"""Kiểm thử API, nghiệp vụ, phân quyền và validation cho Quản lý Travel (Admin CRUD)."""

from datetime import timedelta
from decimal import Decimal
from pathlib import Path
import sys
import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.modules.travel.models import TravelPlace, TravelRegion
from app.modules.users.models import Role, User


class TestTravelManagement(unittest.TestCase):
    """Kiểm thử CRUD quản trị địa điểm du lịch và phân quyền chỉ ADMIN."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.TestingSessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=cls.engine,
        )
        Base.metadata.create_all(bind=cls.engine)

        def override_get_db():
            db = cls.TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        cls._previous_get_db = app.dependency_overrides.get(get_db)
        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls) -> None:
        if cls._previous_get_db is not None:
            app.dependency_overrides[get_db] = cls._previous_get_db
        else:
            app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=cls.engine)

    def setUp(self) -> None:
        self.db = self.TestingSessionLocal()
        self.db.query(TravelPlace).delete()
        self.db.query(User).delete()
        self.db.query(Role).delete()
        self.db.commit()

        role_user = Role(id=1, name="USER", description="Standard user")
        role_admin = Role(id=2, name="ADMIN", description="Administrator")
        self.db.add_all([role_user, role_admin])
        self.db.commit()

        pw_hash = hash_password("Password@123")
        self.normal_user = User(
            id=10,
            username="normal_user",
            email="user@test.local",
            password_hash=pw_hash,
            role_id=role_user.id,
        )
        self.admin_user = User(
            id=20,
            username="admin_user",
            email="admin@test.local",
            password_hash=pw_hash,
            role_id=role_admin.id,
        )
        self.db.add_all([self.normal_user, self.admin_user])
        self.db.commit()

        self.user_token = create_access_token(user_id=self.normal_user.id)
        self.admin_token = create_access_token(user_id=self.admin_user.id)
        self.user_headers = {"Authorization": f"Bearer {self.user_token}"}
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}

        self.place_active = TravelPlace(
            id=1,
            name="Phố cổ Hội An",
            province_city="Quảng Nam",
            region=TravelRegion.TRUNG,
            estimated_cost=500000,
            estimated_duration=Decimal("8.0"),
            activity_type="Văn hóa lịch sử",
            highlights="Thả đèn hoa đăng, Check-in Chùa Cầu",
            description="Đô thị cổ di sản thế giới.",
            image_url="https://example.com/hoian.jpg",
            rating=Decimal("4.8"),
            is_active=True,
        )
        self.place_inactive = TravelPlace(
            id=2,
            name="Đảo Cô Tô",
            province_city="Quảng Ninh",
            region=TravelRegion.BAC,
            estimated_cost=1200000,
            estimated_duration=Decimal("24.0"),
            activity_type="Nghỉ dưỡng biển",
            highlights="Tắm biển Hồng Vàn, Ngắm bình minh",
            description="Đảo nghỉ dưỡng phía Bắc.",
            image_url=None,
            rating=Decimal("4.5"),
            is_active=False,
        )
        self.db.add_all([self.place_active, self.place_inactive])
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()

    def _assert_error_envelope(
        self,
        body: dict,
        *,
        error_code: str,
        path: str,
    ) -> None:
        self.assertEqual(
            set(body.keys()),
            {"success", "message", "data", "error_code", "errors", "path"},
        )
        self.assertFalse(body["success"])
        self.assertEqual(body["error_code"], error_code)
        self.assertEqual(body["path"], path)

    def _valid_payload(self, **overrides) -> dict:
        payload = {
            "name": "  Thác Bản Giốc  ",
            "province_city": "  Cao Bằng  ",
            "region": "Bắc",
            "estimated_cost": 450000,
            "estimated_duration": 6.5,
            "activity_type": "  Khám phá thiên nhiên  ",
            "highlights": ["Chèo bè ngắm thác", "Check-in biên giới", "Chèo bè ngắm thác"],
            "description": "  Thác nước hùng vĩ vùng Đông Bắc.  ",
            "image_url": "https://example.com/bangioc.jpg",
            "rating": 4.7,
            "is_active": True,
        }
        payload.update(overrides)
        return payload

    # ------------------------------------------------------------------
    # Authorization & Public Recommend Isolation
    # ------------------------------------------------------------------

    def test_missing_or_invalid_token_returns_401_across_all_crud_endpoints(self) -> None:
        expired = create_access_token(
            user_id=self.admin_user.id,
            expires_delta=timedelta(minutes=-5),
        )
        endpoints = [
            ("GET", "/api/v1/travel", None),
            ("GET", "/api/v1/travel/1", None),
            ("POST", "/api/v1/travel", self._valid_payload()),
            ("PUT", "/api/v1/travel/1", self._valid_payload()),
            ("PATCH", "/api/v1/travel/1", {"estimated_cost": 600000}),
            ("DELETE", "/api/v1/travel/1", None),
        ]
        for method, path, payload in endpoints:
            for headers in ({}, {"Authorization": "Bearer invalid.jwt.token"}, {"Authorization": f"Bearer {expired}"}):
                res = self.client.request(method, path, json=payload, headers=headers)
                self.assertEqual(res.status_code, 401, f"{method} {path} should return 401")
                self._assert_error_envelope(res.json(), error_code="UNAUTHORIZED", path=path)

    def test_non_admin_user_returns_403_across_all_crud_endpoints(self) -> None:
        endpoints = [
            ("GET", "/api/v1/travel", None),
            ("GET", "/api/v1/travel/1", None),
            ("POST", "/api/v1/travel", self._valid_payload()),
            ("PUT", "/api/v1/travel/1", self._valid_payload()),
            ("PATCH", "/api/v1/travel/1", {"estimated_cost": 600000}),
            ("DELETE", "/api/v1/travel/1", None),
        ]
        for method, path, payload in endpoints:
            res = self.client.request(method, path, json=payload, headers=self.user_headers)
            self.assertEqual(res.status_code, 403, f"{method} {path} should return 403 for USER")
            self._assert_error_envelope(res.json(), error_code="FORBIDDEN", path=path)

    def test_public_recommend_endpoint_remains_accessible_without_auth(self) -> None:
        res = self.client.post("/api/v1/travel/recommend", json={"limit": 5})
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        self.assertEqual(len(body["data"]["items"]), 1)
        self.assertEqual(body["data"]["items"][0]["name"], "Phố cổ Hội An")

    # ------------------------------------------------------------------
    # CRUD Happy Paths
    # ------------------------------------------------------------------

    def test_admin_list_places_supports_filters_pagination_and_inactive(self) -> None:
        res_all = self.client.get("/api/v1/travel", headers=self.admin_headers)
        self.assertEqual(res_all.status_code, 200)
        data = res_all.json()["data"]
        self.assertEqual(data["total"], 2)
        self.assertEqual(len(data["items"]), 2)
        self.assertEqual(data["items"][0]["highlights"], ["Thả đèn hoa đăng", "Check-in Chùa Cầu"])

        res_kw = self.client.get(
            "/api/v1/travel",
            params={"keyword": "Quảng", "region": "Bắc", "is_active": False},
            headers=self.admin_headers,
        )
        self.assertEqual(res_kw.status_code, 200)
        filtered = res_kw.json()["data"]
        self.assertEqual(filtered["total"], 1)
        self.assertEqual(filtered["items"][0]["name"], "Đảo Cô Tô")

        res_page = self.client.get(
            "/api/v1/travel",
            params={"limit": 1, "offset": 1},
            headers=self.admin_headers,
        )
        self.assertEqual(res_page.status_code, 200)
        paged = res_page.json()["data"]
        self.assertEqual(paged["total"], 2)
        self.assertEqual(paged["limit"], 1)
        self.assertEqual(paged["offset"], 1)
        self.assertEqual(len(paged["items"]), 1)
        self.assertEqual(paged["items"][0]["id"], 2)

    def test_admin_get_place_detail_returns_active_and_inactive(self) -> None:
        for place_id, expected_name in ((1, "Phố cổ Hội An"), (2, "Đảo Cô Tô")):
            res = self.client.get(f"/api/v1/travel/{place_id}", headers=self.admin_headers)
            self.assertEqual(res.status_code, 200)
            body = res.json()
            self.assertTrue(body["success"])
            self.assertEqual(body["data"]["name"], expected_name)

    def test_admin_create_place_list_and_string_highlights(self) -> None:
        res = self.client.post(
            "/api/v1/travel",
            json=self._valid_payload(),
            headers=self.admin_headers,
        )
        self.assertEqual(res.status_code, 201)
        created = res.json()["data"]
        self.assertEqual(created["name"], "Thác Bản Giốc")
        self.assertEqual(created["province_city"], "Cao Bằng")
        self.assertEqual(created["activity_type"], "Khám phá thiên nhiên")
        self.assertEqual(created["highlights"], ["Chèo bè ngắm thác", "Check-in biên giới"])
        self.assertEqual(created["description"], "Thác nước hùng vĩ vùng Đông Bắc.")
        self.assertEqual(created["estimated_cost"], 450000)
        self.assertEqual(created["estimated_duration"], 6.5)
        self.assertEqual(created["rating"], 4.7)

        res_str = self.client.post(
            "/api/v1/travel",
            json=self._valid_payload(
                name="Hồ Ba Bể",
                province_city="Bắc Kạn",
                highlights="Đi thuyền trên hồ, Thăm động Puông\nNgủ homestay",
                image_url="   ",
                description="   ",
            ),
            headers=self.admin_headers,
        )
        self.assertEqual(res_str.status_code, 201)
        created2 = res_str.json()["data"]
        self.assertEqual(
            created2["highlights"],
            ["Đi thuyền trên hồ", "Thăm động Puông", "Ngủ homestay"],
        )
        self.assertIsNone(created2["image_url"])
        self.assertIsNone(created2["description"])

    def test_admin_put_replaces_all_fields(self) -> None:
        put_payload = {
            "name": "Phố cổ Hội An Mới",
            "province_city": "Quảng Nam",
            "region": "Trung",
            "estimated_cost": 750000,
            "estimated_duration": 10.0,
            "activity_type": "Nghỉ dưỡng sinh thái",
            "highlights": ["Đi thuyền sông Hoài"],
            "description": None,
            "image_url": None,
            "rating": 4.9,
            "is_active": False,
        }
        res = self.client.put("/api/v1/travel/1", json=put_payload, headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        updated = res.json()["data"]
        self.assertEqual(updated["name"], "Phố cổ Hội An Mới")
        self.assertEqual(updated["estimated_cost"], 750000)
        self.assertEqual(updated["estimated_duration"], 10.0)
        self.assertEqual(updated["highlights"], ["Đi thuyền sông Hoài"])
        self.assertIsNone(updated["description"])
        self.assertIsNone(updated["image_url"])
        self.assertFalse(updated["is_active"])

    def test_admin_patch_updates_partial_and_clears_nullable_fields(self) -> None:
        res = self.client.patch(
            "/api/v1/travel/1",
            json={"estimated_cost": 600000, "description": None, "highlights": None},
            headers=self.admin_headers,
        )
        self.assertEqual(res.status_code, 200)
        updated = res.json()["data"]
        self.assertEqual(updated["name"], "Phố cổ Hội An")
        self.assertEqual(updated["estimated_cost"], 600000)
        self.assertIsNone(updated["description"])
        self.assertEqual(updated["highlights"], [])
        self.assertEqual(updated["image_url"], "https://example.com/hoian.jpg")

    def test_admin_delete_place_removes_record_and_subsequent_get_returns_404(self) -> None:
        res = self.client.delete("/api/v1/travel/2", headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["data"], {"id": 2, "name": "Đảo Cô Tô"})

        res_after = self.client.get("/api/v1/travel/2", headers=self.admin_headers)
        self.assertEqual(res_after.status_code, 404)
        self._assert_error_envelope(
            res_after.json(),
            error_code="RESOURCE_NOT_FOUND",
            path="/api/v1/travel/2",
        )

    # ------------------------------------------------------------------
    # Business Errors & Validation
    # ------------------------------------------------------------------

    def test_duplicate_name_returns_409_on_post_put_patch(self) -> None:
        res_post = self.client.post(
            "/api/v1/travel",
            json=self._valid_payload(name="phố cổ hội an"),
            headers=self.admin_headers,
        )
        self.assertEqual(res_post.status_code, 409)
        self._assert_error_envelope(res_post.json(), error_code="CONFLICT", path="/api/v1/travel")

        res_put = self.client.put(
            "/api/v1/travel/2",
            json=self._valid_payload(name="Phố cổ Hội An"),
            headers=self.admin_headers,
        )
        self.assertEqual(res_put.status_code, 409)
        self._assert_error_envelope(res_put.json(), error_code="CONFLICT", path="/api/v1/travel/2")

        res_patch = self.client.patch(
            "/api/v1/travel/2",
            json={"name": "PHỐ CỔ HỘI AN"},
            headers=self.admin_headers,
        )
        self.assertEqual(res_patch.status_code, 409)
        self._assert_error_envelope(res_patch.json(), error_code="CONFLICT", path="/api/v1/travel/2")

    def test_missing_id_returns_404_for_get_put_patch_delete(self) -> None:
        cases = [
            ("GET", "/api/v1/travel/999", None),
            ("PUT", "/api/v1/travel/999", self._valid_payload()),
            ("PATCH", "/api/v1/travel/999", {"estimated_cost": 100000}),
            ("DELETE", "/api/v1/travel/999", None),
        ]
        for method, path, payload in cases:
            res = self.client.request(method, path, json=payload, headers=self.admin_headers)
            self.assertEqual(res.status_code, 404)
            self._assert_error_envelope(res.json(), error_code="RESOURCE_NOT_FOUND", path=path)

    def test_empty_patch_payload_returns_400_bad_request(self) -> None:
        res = self.client.patch("/api/v1/travel/1", json={}, headers=self.admin_headers)
        self.assertEqual(res.status_code, 400)
        self._assert_error_envelope(res.json(), error_code="BAD_REQUEST", path="/api/v1/travel/1")

    def test_validation_errors_return_422_with_standard_envelope(self) -> None:
        invalid_payloads = [
            self._valid_payload(name="   "),
            self._valid_payload(province_city=""),
            self._valid_payload(activity_type="   "),
            self._valid_payload(region="Miền Đông"),
            self._valid_payload(estimated_cost=-1000),
            self._valid_payload(estimated_cost=True),
            self._valid_payload(estimated_duration=0),
            self._valid_payload(estimated_duration=0.01),
            self._valid_payload(estimated_duration=1000.0),
            self._valid_payload(rating=0.5),
            self._valid_payload(rating=5.5),
            self._valid_payload(image_url="ftp://example.com/a.jpg"),
            self._valid_payload(unexpected_field="hack"),
        ]
        for payload in invalid_payloads:
            res = self.client.post("/api/v1/travel", json=payload, headers=self.admin_headers)
            self.assertEqual(res.status_code, 422, f"Expected 422 for payload={payload}")
            body = res.json()
            self._assert_error_envelope(body, error_code="VALIDATION_ERROR", path="/api/v1/travel")
            self.assertTrue(body["errors"])

        # PATCH explicit null on non-nullable fields must fail with 422
        for field in ("name", "province_city", "region", "estimated_cost", "estimated_duration", "activity_type", "rating", "is_active"):
            res_null = self.client.patch("/api/v1/travel/1", json={field: None}, headers=self.admin_headers)
            self.assertEqual(res_null.status_code, 422, f"Expected 422 for PATCH {field}=None")

        # Invalid path id <= 0
        res_id = self.client.get("/api/v1/travel/0", headers=self.admin_headers)
        self.assertEqual(res_id.status_code, 422)


if __name__ == "__main__":
    unittest.main()
