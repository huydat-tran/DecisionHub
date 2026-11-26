"""Kiểm thử tự động Nhóm B: API Lịch sử quyết định (TC05 -> TC10, TC13, TC14).

Kiểm tra các endpoint thực tế trong dự án:
- GET /decisions/history
- GET /api/v1/decisions/history
- GET /decisions/history/{decision_id}
- GET /api/v1/decisions/history/{decision_id}

Đặc biệt kiểm tra bảo mật (IDOR / Broken Object Level Authorization):
- User A chỉ xem được lịch sử của User A.
- User B chỉ xem được lịch sử của User B.
- User A cố truy cập `decision_id` của User B -> bị từ chối với HTTP 404 (RESOURCE_NOT_FOUND),
  tuyệt đối không lộ dữ liệu của User B.
"""

import json
import sys
import unittest
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from starlette.requests import Request

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.common.exceptions import DecisionHubException, build_error_response
from app.core.database import Base
from app.core.security import create_access_token, hash_password
from app.modules.auth.dependencies import get_current_user
from app.modules.decision.models import Decision, DecisionCriterion, HardConstraint
from app.modules.decision.router import (
    get_decision_history_detail,
    get_decision_history_list,
    recommend_decisions,
)
from app.modules.decision.schema import DecisionRecommendRequest
from app.modules.food.models_food import Food, FoodIngredient, Ingredient
from app.modules.users.models import Role, User


def _make_get_request(path: str) -> Request:
    """Tạo đối tượng Request GET để kiểm tra cấu trúc JSON lỗi chuẩn của dự án."""
    scope = {
        "type": "http",
        "method": "GET",
        "path": path,
        "headers": [],
        "query_string": b"",
    }
    return Request(scope)


class TestDecisionHistoryAPI(unittest.TestCase):
    """Kiểm thử API Lịch sử quyết định và phân quyền bảo mật giữa các User (TC05 -> TC10, TC13, TC14)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=cls.engine)
        cls.SessionLocal = sessionmaker(
            bind=cls.engine,
            autoflush=False,
            autocommit=False,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        Base.metadata.drop_all(bind=cls.engine)

    def setUp(self) -> None:
        self.db: Session = self.SessionLocal()

        # Xóa sạch dữ liệu trước mỗi test case
        self.db.query(Decision).delete()
        self.db.query(FoodIngredient).delete()
        self.db.query(Food).delete()
        self.db.query(Ingredient).delete()
        self.db.query(DecisionCriterion).delete()
        self.db.query(HardConstraint).delete()
        self.db.query(User).delete()
        self.db.query(Role).delete()
        self.db.commit()

        # Tạo Role và 3 tài khoản test độc lập: User A, User B, User C (chưa có lịch sử)
        self.role_user = Role(id=1, name="USER", description="Standard User")
        self.db.add(self.role_user)
        self.db.commit()

        self.user_a = User(
            id=201,
            username="tester_user_a",
            email="tester_a@test.local",
            password_hash=hash_password("QaTest@123"),
            role_id=self.role_user.id,
        )
        self.user_b = User(
            id=202,
            username="tester_user_b",
            email="tester_b@test.local",
            password_hash=hash_password("QaTest@123"),
            role_id=self.role_user.id,
        )
        self.user_c = User(
            id=203,
            username="tester_user_c",
            email="tester_c@test.local",
            password_hash=hash_password("QaTest@123"),
            role_id=self.role_user.id,
        )
        self.db.add_all([self.user_a, self.user_b, self.user_c])
        self.db.commit()

        # Token riêng cho từng user
        self.token_a = create_access_token(user_id=self.user_a.id)
        self.token_b = create_access_token(user_id=self.user_b.id)
        self.token_c = create_access_token(user_id=self.user_c.id)

        # Seed tiêu chí WSM và Hard Constraints
        self.db.add_all(
            [
                DecisionCriterion(
                    id=1,
                    domain="food",
                    name="Giá",
                    direction="min",
                    weight=Decimal("0.4000"),
                ),
                DecisionCriterion(
                    id=2,
                    domain="food",
                    name="Mức phù hợp nhu cầu/khẩu vị",
                    direction="max",
                    weight=Decimal("0.3500"),
                ),
                DecisionCriterion(
                    id=3,
                    domain="food",
                    name="Thời gian chuẩn bị",
                    direction="min",
                    weight=Decimal("0.2500"),
                ),
            ]
        )
        self.db.add_all(
            [
                HardConstraint(
                    id=1,
                    domain="food",
                    name="Ngân sách tối đa",
                    field_name="price",
                    operator="<=",
                    is_active=True,
                ),
                HardConstraint(
                    id=2,
                    domain="food",
                    name="Loại bữa ăn",
                    field_name="meal_type",
                    operator="=",
                    is_active=True,
                ),
            ]
        )

        # Seed món ăn test
        ing_bo = Ingredient(id=1, name="Thịt bò")
        ing_heo = Ingredient(id=2, name="Thịt heo")
        self.db.add_all([ing_bo, ing_heo])
        self.db.commit()

        food1 = Food(
            id=1,
            name="Phở bò tái",
            price=Decimal("45000.00"),
            meal_type="breakfast",
            prep_time=15,
            tags=["truyền thống", "nước"],
            is_active=True,
        )
        food1.ingredients = [ing_bo]

        food2 = Food(
            id=2,
            name="Bún chả Hà Nội",
            price=Decimal("35000.00"),
            meal_type="lunch",
            prep_time=20,
            tags=["truyền thống", "đậm đà"],
            is_active=True,
        )
        food2.ingredients = [ing_heo]

        self.db.add_all([food1, food2])
        self.db.commit()

        # Tạo dữ liệu lịch sử thực tế qua API Recommend cho User A (2 quyết định) và User B (1 quyết định)
        recommend_decisions(
            payload=DecisionRecommendRequest(
                budget_max=40000,
                meal_type="lunch",
                preferred_tags=["truyền thống"],
            ),
            db=self.db,
            current_user=self.user_a,
        )
        recommend_decisions(
            payload=DecisionRecommendRequest(
                budget_max=60000,
                meal_type="breakfast",
                preferred_tags=["nước"],
            ),
            db=self.db,
            current_user=self.user_a,
        )
        recommend_decisions(
            payload=DecisionRecommendRequest(
                budget_max=50000,
                meal_type="lunch",
                preferred_tags=["đậm đà"],
            ),
            db=self.db,
            current_user=self.user_b,
        )

        # Gán mốc thời gian rõ ràng để kiểm tra sắp xếp created_at DESC
        a_records = (
            self.db.query(Decision)
            .filter(Decision.user_id == self.user_a.id)
            .order_by(Decision.id.asc())
            .all()
        )
        a_records[0].created_at = datetime(2026, 11, 25, 9, 0, 0)
        a_records[1].created_at = datetime(2026, 11, 25, 10, 30, 0)
        self.db.commit()

        self.user_a_decision_ids = [r.id for r in a_records]
        b_record = (
            self.db.query(Decision)
            .filter(Decision.user_id == self.user_b.id)
            .first()
        )
        self.user_b_decision_id = b_record.id

    def tearDown(self) -> None:
        self.db.rollback()
        self.db.close()

    def _call_history_list_api(
        self,
        token: str | None,
        limit: int = 20,
        offset: int = 0,
        path: str = "/decisions/history",
    ) -> tuple[int, dict[str, Any]]:
        """Mô phỏng gọi GET /decisions/history kèm xác thực JWT và chuẩn hóa lỗi."""
        request = _make_get_request(path)
        try:
            credentials = (
                HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
                if token is not None
                else None
            )
            current_user = get_current_user(credentials=credentials, db=self.db)
            resp = get_decision_history_list(
                limit=limit,
                offset=offset,
                db=self.db,
                current_user=current_user,
            )
            return 200, resp.model_dump(mode="json")
        except DecisionHubException as exc:
            err_resp = build_error_response(
                request=request,
                status_code=exc.status_code,
                message=exc.message,
                error_code=exc.error_code,
                data=exc.data,
                errors=exc.errors,
            )
            return err_resp.status_code, json.loads(bytes(err_resp.body).decode("utf-8"))

    def _call_history_detail_api(
        self,
        decision_id: int,
        token: str | None,
        path: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        """Mô phỏng gọi GET /decisions/history/{decision_id} kèm xác thực JWT và chuẩn hóa lỗi."""
        actual_path = path or f"/decisions/history/{decision_id}"
        request = _make_get_request(actual_path)
        try:
            credentials = (
                HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
                if token is not None
                else None
            )
            current_user = get_current_user(credentials=credentials, db=self.db)
            resp = get_decision_history_detail(
                decision_id=decision_id,
                db=self.db,
                current_user=current_user,
            )
            return 200, resp.model_dump(mode="json")
        except DecisionHubException as exc:
            err_resp = build_error_response(
                request=request,
                status_code=exc.status_code,
                message=exc.message,
                error_code=exc.error_code,
                data=exc.data,
                errors=exc.errors,
            )
            return err_resp.status_code, json.loads(bytes(err_resp.body).decode("utf-8"))

    # ------------------------------------------------------------------
    # TC05: User A lấy danh sách lịch sử của chính mình
    # ------------------------------------------------------------------
    def test_tc05_user_a_gets_own_decision_history_list(self) -> None:
        """TC05: User A gọi GET /decisions/history -> chỉ trả về 2 bản ghi của User A, mới nhất trước."""
        status_code, body = self._call_history_list_api(token=self.token_a)

        self.assertEqual(status_code, 200)
        self.assertTrue(body["success"])
        self.assertEqual(body["total"], 2)
        self.assertEqual(len(body["data"]), 2)

        # Kiểm tra tất cả bản ghi đều thuộc về User A, không có bản ghi của User B
        for item in body["data"]:
            self.assertEqual(item["user_id"], self.user_a.id)
            self.assertNotEqual(item["id"], self.user_b_decision_id)
            self.assertEqual(item["domain"], "food")
            self.assertIn("input_snapshot", item)
            self.assertIn("result_snapshot", item)
            self.assertIn("created_at", item)

        # Kiểm tra thứ tự created_at DESC (quyết định 10:30 đứng trước 09:00)
        self.assertEqual(body["data"][0]["id"], self.user_a_decision_ids[1])
        self.assertEqual(body["data"][1]["id"], self.user_a_decision_ids[0])
        self.assertEqual(body["data"][0]["input_snapshot"]["budget_max"], 60000)
        self.assertEqual(body["data"][1]["input_snapshot"]["budget_max"], 40000)

    # ------------------------------------------------------------------
    # TC06: User A xem chi tiết lịch sử của chính mình
    # ------------------------------------------------------------------
    def test_tc06_user_a_gets_own_decision_detail(self) -> None:
        """TC06: User A gọi GET /decisions/history/{decision_id} -> trả về đúng chi tiết quyết định của A."""
        target_id = self.user_a_decision_ids[0]
        status_code, body = self._call_history_detail_api(
            decision_id=target_id,
            token=self.token_a,
        )

        self.assertEqual(status_code, 200)
        self.assertTrue(body["success"])
        self.assertEqual(body["id"], target_id)
        self.assertEqual(body["data"]["id"], target_id)
        self.assertEqual(body["user_id"], self.user_a.id)
        self.assertEqual(body["domain"], "food")
        self.assertEqual(body["input_snapshot"]["budget_max"], 40000)
        self.assertEqual(body["input_snapshot"]["meal_type"], "lunch")
        self.assertEqual(body["result_snapshot"]["items"][0]["name"], "Bún chả Hà Nội")

    # ------------------------------------------------------------------
    # TC07: User A không thể xem lịch sử của User B (Bảo mật IDOR)
    # ------------------------------------------------------------------
    def test_tc07_user_a_cannot_access_user_b_decision_detail(self) -> None:
        """TC07: User A cố truy cập decision_id của User B -> phải trả về 404 RESOURCE_NOT_FOUND, không lộ dữ liệu."""
        status_code, body = self._call_history_detail_api(
            decision_id=self.user_b_decision_id,
            token=self.token_a,
        )

        self.assertEqual(status_code, 404)
        self.assertFalse(body["success"])
        self.assertEqual(body["error_code"], "RESOURCE_NOT_FOUND")
        self.assertNotIn("input_snapshot", body)
        self.assertNotIn("result_snapshot", body)

    # ------------------------------------------------------------------
    # TC08: User B chỉ nhận được lịch sử của User B
    # ------------------------------------------------------------------
    def test_tc08_user_b_only_receives_user_b_history(self) -> None:
        """TC08: User B gọi GET /decisions/history -> chỉ nhận được 1 bản ghi của User B."""
        status_code, body = self._call_history_list_api(token=self.token_b)

        self.assertEqual(status_code, 200)
        self.assertTrue(body["success"])
        self.assertEqual(body["total"], 1)
        self.assertEqual(len(body["data"]), 1)
        self.assertEqual(body["data"][0]["id"], self.user_b_decision_id)
        self.assertEqual(body["data"][0]["user_id"], self.user_b.id)
        self.assertEqual(body["data"][0]["input_snapshot"]["budget_max"], 50000)

        # User B cũng không thể xem chi tiết quyết định của User A
        status_cross, body_cross = self._call_history_detail_api(
            decision_id=self.user_a_decision_ids[0],
            token=self.token_b,
        )
        self.assertEqual(status_cross, 404)
        self.assertFalse(body_cross["success"])

    # ------------------------------------------------------------------
    # TC09: Lấy lịch sử khi thiếu token
    # ------------------------------------------------------------------
    def test_tc09_access_history_without_token_returns_401(self) -> None:
        """TC09: Gọi GET /decisions/history và GET /decisions/history/{id} không có token -> trả về 401."""
        status_list, body_list = self._call_history_list_api(token=None)
        self.assertEqual(status_list, 401)
        self.assertFalse(body_list["success"])
        self.assertEqual(body_list["error_code"], "UNAUTHORIZED")
        self.assertIn("vui lòng đăng nhập", body_list["message"].lower())

        status_detail, body_detail = self._call_history_detail_api(
            decision_id=self.user_a_decision_ids[0],
            token=None,
        )
        self.assertEqual(status_detail, 401)
        self.assertFalse(body_detail["success"])
        self.assertEqual(body_detail["error_code"], "UNAUTHORIZED")

    # ------------------------------------------------------------------
    # TC10: Truy cập decision_id không tồn tại
    # ------------------------------------------------------------------
    def test_tc10_access_non_existent_decision_id_returns_404(self) -> None:
        """TC10: User A truy cập decision_id không tồn tại (999999) -> trả về 404 RESOURCE_NOT_FOUND."""
        status_code, body = self._call_history_detail_api(
            decision_id=999999,
            token=self.token_a,
        )

        self.assertEqual(status_code, 404)
        self.assertFalse(body["success"])
        self.assertEqual(body["error_code"], "RESOURCE_NOT_FOUND")
        self.assertEqual(body["data"], {"resource": "Lịch sử quyết định", "id": 999999})

    # ------------------------------------------------------------------
    # TC13 (Bổ sung): Truy cập lịch sử với token không hợp lệ hoặc hết hạn
    # ------------------------------------------------------------------
    def test_tc13_access_history_with_invalid_or_expired_token_returns_401(self) -> None:
        """TC13: Gọi API lịch sử với token giả mạo hoặc đã hết hạn -> trả về 401 UNAUTHORIZED."""
        status_bad, body_bad = self._call_history_list_api(token="invalid.token.value")
        self.assertEqual(status_bad, 401)
        self.assertFalse(body_bad["success"])
        self.assertEqual(body_bad["error_code"], "UNAUTHORIZED")

        expired_token = create_access_token(
            user_id=self.user_a.id,
            expires_delta=timedelta(minutes=-5),
        )
        status_exp, body_exp = self._call_history_detail_api(
            decision_id=self.user_a_decision_ids[0],
            token=expired_token,
        )
        self.assertEqual(status_exp, 401)
        self.assertFalse(body_exp["success"])
        self.assertEqual(body_exp["error_code"], "UNAUTHORIZED")

    # ------------------------------------------------------------------
    # TC14 (Bổ sung): User chưa từng recommend lấy danh sách lịch sử
    # ------------------------------------------------------------------
    def test_tc14_user_with_no_history_receives_empty_list(self) -> None:
        """TC14: User C chưa từng recommend gọi GET /decisions/history -> trả về 200, data=[], total=0."""
        status_code, body = self._call_history_list_api(token=self.token_c)

        self.assertEqual(status_code, 200)
        self.assertTrue(body["success"])
        self.assertEqual(body["total"], 0)
        self.assertEqual(body["data"], [])
        self.assertEqual(body["items"], [])


if __name__ == "__main__":
    unittest.main()

