"""Kiểm thử tự động Nhóm A: API Recommend (TC01, TC02, TC03, TC04, TC11, TC12).

Kiểm tra các endpoint thực tế trong dự án:
- POST /decisions/food/recommend
- POST /api/v1/decisions/food/recommend
- POST /decisions/recommend
- POST /api/v1/decisions/recommend

Đảm bảo:
- Chạy độc lập, lặp lại được nhiều lần trên SQLite in-memory (không ảnh hưởng dữ liệu thật).
- Kiểm tra đầy đủ HTTP Status Code, cấu trúc JSON response, kết quả WSM,
  cơ chế xác thực JWT (có token, thiếu token, token sai/hết hạn) và việc lưu bảng `decisions`.
"""

import json
import sys
import unittest
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from fastapi.exceptions import RequestValidationError
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from starlette.requests import Request

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.common.exceptions import (
    DecisionHubException,
     _serialize_validation_errors,
    build_error_response,
)
from app.core.database import Base
from app.core.security import create_access_token, hash_password
from app.modules.decision.models import Decision, DecisionCriterion, HardConstraint
from app.modules.decision.router import get_optional_current_user, recommend_decisions
from app.modules.decision.schema import DecisionRecommendRequest
from app.modules.food.models_food import Food, FoodIngredient, Ingredient
from app.modules.users.models import Role, User


def _make_dummy_request(path: str = "/decisions/food/recommend") -> Request:
    """Tạo đối tượng Request phục vụ kiểm tra chuẩn hóa JSON lỗi từ exception handler."""
    scope = {
        "type": "http",
        "method": "POST",
        "path": path,
        "headers": [],
        "query_string": b"",
    }
    return Request(scope)


class TestRecommendAPI(unittest.TestCase):
    """Kiểm thử API Recommend (TC01 -> TC04, TC11, TC12)."""

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

        # Reset toàn bộ dữ liệu test trước mỗi test case
        self.db.query(Decision).delete()
        self.db.query(FoodIngredient).delete()
        self.db.query(Food).delete()
        self.db.query(Ingredient).delete()
        self.db.query(DecisionCriterion).delete()
        self.db.query(HardConstraint).delete()
        self.db.query(User).delete()
        self.db.query(Role).delete()
        self.db.commit()

        # Tạo Role và 2 tài khoản test độc lập User A, User B
        self.role_user = Role(id=1, name="USER", description="Standard User")
        self.db.add(self.role_user)
        self.db.commit()

        self.user_a = User(
            id=101,
            username="qa_user_a",
            email="qa_user_a@test.local",
            password_hash=hash_password("QaTest@123"),
            role_id=self.role_user.id,
        )
        self.user_b = User(
            id=102,
            username="qa_user_b",
            email="qa_user_b@test.local",
            password_hash=hash_password("QaTest@123"),
            role_id=self.role_user.id,
        )
        self.db.add_all([self.user_a, self.user_b])
        self.db.commit()

        # Seed tiêu chí WSM mặc định cho domain 'food' (Tổng trọng số = 1.0)
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

        # Seed điều kiện lọc bắt buộc (Hard Constraints) cho domain 'food'
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
                HardConstraint(
                    id=3,
                    domain="food",
                    name="Thời gian chuẩn bị tối đa",
                    field_name="prep_time",
                    operator="<=",
                    is_active=True,
                ),
                HardConstraint(
                    id=4,
                    domain="food",
                    name="Nguyên liệu cần tránh",
                    field_name="ingredients",
                    operator="not_in",
                    is_active=True,
                ),
            ]
        )

        # Seed nguyên liệu và danh sách món ăn test
        ing_bo = Ingredient(id=1, name="Thịt bò")
        ing_heo = Ingredient(id=2, name="Thịt heo")
        ing_dau = Ingredient(id=3, name="Đậu phộng")
        ing_nam = Ingredient(id=4, name="Nấm hương")
        self.db.add_all([ing_bo, ing_heo, ing_dau, ing_nam])
        self.db.commit()

        food_bun_cha = Food(
            id=1,
            name="Bún chả Hà Nội",
            price=Decimal("35000.00"),
            meal_type="lunch",
            prep_time=20,
            tags=["truyền thống", "đậm đà"],
            is_active=True,
        )
        food_bun_cha.ingredients = [ing_heo]

        food_com_chay = Food(
            id=2,
            name="Cơm chiên đậu hũ nấm",
            price=Decimal("30000.00"),
            meal_type="lunch",
            prep_time=12,
            tags=["chay", "thanh đạm", "nhanh"],
            is_active=True,
        )
        food_com_chay.ingredients = [ing_nam]

        food_com_tam = Food(
            id=3,
            name="Cơm tấm sườn bì chả",
            price=Decimal("55000.00"),
            meal_type="lunch",
            prep_time=15,
            tags=["đậm đà", "cơm"],
            is_active=True,
        )
        food_com_tam.ingredients = [ing_heo, ing_dau]

        self.db.add_all([food_bun_cha, food_com_chay, food_com_tam])
        self.db.commit()

    def tearDown(self) -> None:
        self.db.rollback()
        self.db.close()

    def _call_recommend_api(
        self,
        raw_body: dict[str, Any],
        token: str | None = None,
        path: str = "/decisions/food/recommend",
    ) -> tuple[int, dict[str, Any]]:
        """Mô phỏng đầy đủ luồng HTTP POST tới endpoint Recommend:
        1. Xác thực Bearer Token qua dependency `get_optional_current_user`.
        2. Validate request body qua `DecisionRecommendRequest` (trả 422 nếu lỗi).
        3. Gọi router handler `recommend_decisions`.
        4. Chuẩn hóa lỗi qua `build_error_response` nếu phát sinh `DecisionHubException`.
        """
        request = _make_dummy_request(path=path)
        try:
            credentials = (
                HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
                if token is not None
                else None
            )
            current_user = get_optional_current_user(
                credentials=credentials,
                db=self.db,
            )

            try:
                payload = DecisionRecommendRequest.model_validate(raw_body)
            except ValidationError as val_exc:
                req_val_err = RequestValidationError(val_exc.errors())
                err_resp = build_error_response(
                    request=request,
                    status_code=422,
                    message="Dữ liệu đầu vào không hợp lệ",
                    error_code="VALIDATION_ERROR",
                    errors=_serialize_validation_errors(req_val_err),
                )
                return err_resp.status_code, json.loads(bytes(err_resp.body).decode("utf-8"))

            resp_model = recommend_decisions(
                payload=payload,
                db=self.db,
                current_user=current_user,
            )
            return 200, resp_model.model_dump(mode="json")

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
    # TC01: Recommend với input hợp lệ và có kết quả (User A đã đăng nhập)
    # ------------------------------------------------------------------
    def test_tc01_recommend_valid_input_with_candidates_and_saves_history(self) -> None:
        """TC01: Recommend với input hợp lệ (có JWT token) trả về 200, xếp hạng WSM và lưu lịch sử."""
        token_a = create_access_token(user_id=self.user_a.id)
        request_body = {
            "budget_max": 50000,
            "meal_type": "lunch",
            "max_prep_time": 25,
            "excluded_ingredients": ["đậu phộng"],
            "preferred_tags": ["truyền thống"],
            "limit": 5,
        }

        status_code, body = self._call_recommend_api(request_body, token=token_a)

        # 1. Kiểm tra HTTP Status & Cấu trúc response
        self.assertEqual(status_code, 200)
        self.assertTrue(body["success"])
        self.assertTrue(body["has_valid_candidates"])
        self.assertEqual(body["total"], 2)
        self.assertEqual(body["total_excluded"], 1)
        self.assertEqual(body["limit"], 5)

        # 2. Kiểm tra danh sách gợi ý phù hợp điều kiện (giá <= 50.000, meal_type = lunch, prep_time <= 25)
        items = body["items"]
        self.assertEqual(len(items), 2)
        for idx, item in enumerate(items, start=1):
            self.assertEqual(item["rank"], idx)
            self.assertLessEqual(item["price"], 50000)
            self.assertEqual(item["meal_type"], "lunch")
            self.assertLessEqual(item["prep_time"], 25)
            self.assertGreaterEqual(item["total_score"], 0.0)
            self.assertLessEqual(item["total_score"], 100.0)
            self.assertIn("price", item["criteria_scores"])
            self.assertIn("preference", item["criteria_scores"])
            self.assertIn("prep_time", item["criteria_scores"])
            self.assertTrue(len(item["reasons"]) >= 1)

        # Điểm xếp hạng giảm dần
        self.assertGreaterEqual(items[0]["total_score"], items[1]["total_score"])

        # 3. Kiểm tra phương án bị loại (Cơm tấm sườn bì chả 55.000đ > 50.000đ và có đậu phộng)
        self.assertEqual(len(body["excluded_items"]), 1)
        self.assertEqual(body["excluded_items"][0]["name"], "Cơm tấm sườn bì chả")
        self.assertEqual(body["excluded_items"][0]["status"], "excluded")

        # 4. Kiểm tra đã lưu đúng 1 bản ghi lịch sử vào bảng decisions cho User A
        saved_records = self.db.query(Decision).all()
        self.assertEqual(len(saved_records), 1)
        saved = saved_records[0]
        self.assertEqual(saved.user_id, self.user_a.id)
        self.assertEqual(saved.domain, "food")
        self.assertEqual(saved.input_snapshot["budget_max"], 50000)
        self.assertEqual(saved.result_snapshot["total"], 2)
        self.assertEqual(saved.result_snapshot["items"][0]["name"], items[0]["name"])

    # ------------------------------------------------------------------
    # TC02: Recommend khi không còn ứng viên phù hợp
    # ------------------------------------------------------------------
    def test_tc02_recommend_when_no_valid_candidates_remain(self) -> None:
        """TC02: Khi ngân sách quá thấp (10.000đ) khiến mọi món bị loại -> trả về 200, items=[], thông báo phù hợp."""
        token_a = create_access_token(user_id=self.user_a.id)
        request_body = {
            "budget_max": 10000,
            "meal_type": "lunch",
            "limit": 5,
        }

        status_code, body = self._call_recommend_api(request_body, token=token_a)

        self.assertEqual(status_code, 200)
        self.assertTrue(body["success"])
        self.assertFalse(body["has_valid_candidates"])
        self.assertEqual(body["total"], 0)
        self.assertEqual(body["items"], [])
        self.assertEqual(body["total_excluded"], 3)
        self.assertEqual(len(body["excluded_items"]), 3)
        self.assertIn("không có phương án hợp lệ", body["message"].lower())

        # Bản ghi lịch sử vẫn lưu đúng trạng thái 0 ứng viên hợp lệ cho User A
        saved = self.db.query(Decision).first()
        self.assertIsNotNone(saved)
        self.assertFalse(saved.result_snapshot["has_valid_candidates"])
        self.assertEqual(saved.result_snapshot["total"], 0)

    # ------------------------------------------------------------------
    # TC03: Recommend khi thiếu Authorization Token (Guest)
    # ------------------------------------------------------------------
    def test_tc03_recommend_without_authorization_token(self) -> None:
        """TC03: Gọi Recommend không truyền token -> trả về 200 cho Guest nhưng KHÔNG lưu lịch sử."""
        request_body = {
            "budget_max": 50000,
            "meal_type": "lunch",
            "limit": 5,
        }

        status_code, body = self._call_recommend_api(request_body, token=None)

        self.assertEqual(status_code, 200)
        self.assertTrue(body["success"])
        self.assertTrue(body["has_valid_candidates"])
        self.assertEqual(body["total"], 2)

        # Kiểm tra bảng decisions KHÔNG có bản ghi nào được tạo
        self.assertEqual(self.db.query(Decision).count(), 0)

    # ------------------------------------------------------------------
    # TC04: Recommend khi token không hợp lệ hoặc đã hết hạn
    # ------------------------------------------------------------------
    def test_tc04_recommend_with_invalid_or_expired_token(self) -> None:
        """TC04: Gửi token sai định dạng hoặc đã hết hạn -> trả về 401 UNAUTHORIZED và không lưu lịch sử."""
        request_body = {
            "budget_max": 50000,
            "meal_type": "lunch",
            "limit": 5,
        }

        # 4a. Token sai chữ ký / định dạng
        status_invalid, body_invalid = self._call_recommend_api(
            request_body,
            token="eyJhbGciOiJIUzI1NiJ9.invalid_payload.invalid_signature",
        )
        self.assertEqual(status_invalid, 401)
        self.assertFalse(body_invalid["success"])
        self.assertEqual(body_invalid["error_code"], "UNAUTHORIZED")
        self.assertIn("không hợp lệ", body_invalid["message"].lower())

        # 4b. Token đã hết hạn
        expired_token = create_access_token(
            user_id=self.user_a.id,
            expires_delta=timedelta(minutes=-10),
        )
        status_expired, body_expired = self._call_recommend_api(
            request_body,
            token=expired_token,
        )
        self.assertEqual(status_expired, 401)
        self.assertFalse(body_expired["success"])
        self.assertEqual(body_expired["error_code"], "UNAUTHORIZED")

        # Đảm bảo không có bản ghi lịch sử nào được lưu
        self.assertEqual(self.db.query(Decision).count(), 0)

    # ------------------------------------------------------------------
    # TC11 (Bổ sung): Recommend với trọng số WSM tùy chỉnh hợp lệ
    # ------------------------------------------------------------------
    def test_tc11_recommend_with_valid_custom_weights(self) -> None:
        """TC11: Recommend với trọng số tùy chỉnh có tổng bằng 1.0 -> áp dụng đúng trọng số mới."""
        token_a = create_access_token(user_id=self.user_a.id)
        custom_weights = {"price": 0.60, "preference": 0.25, "prep_time": 0.15}
        request_body = {
            "budget_max": 50000,
            "meal_type": "lunch",
            "weights": custom_weights,
            "limit": 5,
        }

        status_code, body = self._call_recommend_api(request_body, token=token_a)

        self.assertEqual(status_code, 200)
        self.assertEqual(body["scoring"]["weights"], custom_weights)
        # Cơm chiên đậu hũ nấm (30.000đ, 12 phút) có giá rẻ nhất và nhanh nhất -> đứng hạng 1
        self.assertEqual(body["items"][0]["name"], "Cơm chiên đậu hũ nấm")
        self.assertEqual(body["items"][0]["rank"], 1)

    # ------------------------------------------------------------------
    # TC12 (Bổ sung): Recommend với dữ liệu đầu vào không hợp lệ (422)
    # ------------------------------------------------------------------
    def test_tc12_recommend_with_invalid_payload_returns_422(self) -> None:
        """TC12: Gửi budget_max <= 0, tổng weights != 1.0 hoặc kèm user_id giả mạo -> trả về 422 và không lưu lịch sử."""
        token_a = create_access_token(user_id=self.user_a.id)

        invalid_payloads = [
            {"budget_max": -20000, "meal_type": "lunch"},
            {
                "budget_max": 50000,
                "weights": {"price": 0.5, "preference": 0.5, "prep_time": 0.5},
            },
            {"budget_max": 50000, "user_id": 999},  # extra="forbid" chặn truyền user_id từ body
        ]

        for bad_body in invalid_payloads:
            with self.subTest(bad_body=bad_body):
                status_code, body = self._call_recommend_api(bad_body, token=token_a)
                self.assertEqual(status_code, 422)
                self.assertFalse(body["success"])
                self.assertEqual(body["error_code"], "VALIDATION_ERROR")
                self.assertTrue(len(body["errors"]) > 0)

        self.assertEqual(self.db.query(Decision).count(), 0)


if __name__ == "__main__":
    unittest.main()

