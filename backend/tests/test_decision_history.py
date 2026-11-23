"""Kiểm thử chức năng lưu lịch sử quyết định và API xem lịch sử (Bước 7).

Bao gồm đầy đủ 7 trường hợp:
1. Lưu lịch sử thành công sau khi recommend với JWT của tài khoản A.
2. Xem danh sách lịch sử (GET /decisions/history) chỉ trả về lịch sử của chính người dùng, sắp xếp mới nhất trước.
3. Xem chi tiết lịch sử (GET /decisions/history/{decision_id}) trả đúng dữ liệu đã lưu.
4. Truy cập trái phép: tài khoản B truy cập ID lịch sử của tài khoản A -> trả về 404.
5. Không có lịch sử: người dùng chưa từng recommend -> trả về danh sách rỗng, không lỗi.
6. Chưa đăng nhập / token không hợp lệ -> trả về 401.
7. Recommend thất bại (dữ liệu không hợp lệ hoặc lỗi nghiệp vụ) -> không tạo bản ghi lịch sử sai.
"""

import sys
import unittest
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from fastapi.security import HTTPAuthorizationCredentials
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.common.exceptions import (
    DecisionHubException,
    ResourceNotFoundException,
    UnauthorizedException,
)
from app.core.database import Base
from app.core.security import create_access_token, hash_password
from app.main import app
from app.modules.auth.dependencies import get_current_user
from app.modules.decision.models import Decision, DecisionCriterion, HardConstraint
from app.modules.decision.router import (
    get_decision_history_detail,
    get_decision_history_list,
    get_optional_current_user,
    recommend_decisions,
)
from app.modules.decision.schema import DecisionRecommendRequest
from app.modules.food.models_food import Food, FoodIngredient, Ingredient
from app.modules.users.models import Role, User


class TestDecisionHistory(unittest.TestCase):
    """Kiểm thử toàn diện lưu lịch sử quyết định và các API lịch sử."""

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

        # Dọn sạch dữ liệu trước mỗi test
        self.db.query(Decision).delete()
        self.db.query(FoodIngredient).delete()
        self.db.query(Food).delete()
        self.db.query(Ingredient).delete()
        self.db.query(DecisionCriterion).delete()
        self.db.query(HardConstraint).delete()
        self.db.query(User).delete()
        self.db.query(Role).delete()
        self.db.commit()

        # Tạo role và 2 tài khoản người dùng A, B
        self.role_user = Role(id=1, name="USER", description="Regular user")
        self.db.add(self.role_user)
        self.db.commit()

        self.user_a = User(
            id=1,
            username="user_a",
            email="user_a@example.com",
            password_hash=hash_password("Password@123"),
            role_id=self.role_user.id,
        )
        self.user_b = User(
            id=2,
            username="user_b",
            email="user_b@example.com",
            password_hash=hash_password("Password@123"),
            role_id=self.role_user.id,
        )
        self.db.add_all([self.user_a, self.user_b])
        self.db.commit()

        # Seed tiêu chí WSM mặc định cho domain food
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

        # Seed hard constraints mặc định cho domain food
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

        # Seed món ăn
        ing_bo = Ingredient(id=1, name="Thịt bò")
        ing_heo = Ingredient(id=2, name="Thịt heo")
        self.db.add_all([ing_bo, ing_heo])
        self.db.commit()

        food1 = Food(
            id=1,
            name="Phở bò Hà Nội",
            price=Decimal("45000.00"),
            meal_type="lunch",
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

    def tearDown(self) -> None:
        self.db.rollback()
        self.db.close()

    def _authenticate_with_jwt(self, user: User) -> User:
        """Tạo JWT token thật cho user và xác thực qua dependency get_current_user."""
        token = create_access_token(user_id=user.id)
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token,
        )
        return get_current_user(credentials=credentials, db=self.db)

    def test_routes_registered(self) -> None:
        """Kiểm tra các route recommend và history được đăng ký đầy đủ trên FastAPI app."""
        route_paths = {
            (method, getattr(route, "path", ""))
            for route in app.routes
            for method in getattr(route, "methods", set())
        }
        self.assertIn(("POST", "/decisions/food/recommend"), route_paths)
        self.assertIn(("POST", "/api/v1/decisions/food/recommend"), route_paths)
        self.assertIn(("GET", "/decisions/history"), route_paths)
        self.assertIn(("GET", "/api/v1/decisions/history"), route_paths)
        self.assertIn(("GET", "/decisions/history/{decision_id}"), route_paths)
        self.assertIn(("GET", "/api/v1/decisions/history/{decision_id}"), route_paths)

    # ------------------------------------------------------------------
    # Trường hợp 1: Lưu lịch sử thành công
    # ------------------------------------------------------------------
    def test_case_1_save_history_on_recommend_success(self) -> None:
        """Đăng nhập tài khoản A -> gọi POST /decisions/food/recommend -> lưu đúng 1 bản ghi lịch sử."""
        authed_user_a = self._authenticate_with_jwt(self.user_a)
        payload = DecisionRecommendRequest(
            budget_max=50000,
            meal_type="lunch",
            max_prep_time=25,
            excluded_ingredients=["đậu phộng"],
            preferred_tags=["truyền thống"],
            limit=5,
        )

        response = recommend_decisions(
            payload=payload,
            db=self.db,
            current_user=authed_user_a,
        )

        self.assertTrue(response.success)
        self.assertEqual(response.total, 2)

        # Kiểm tra bảng decisions có đúng 1 bản ghi mới của user_a
        records = self.db.query(Decision).all()
        self.assertEqual(len(records), 1)
        saved = records[0]

        self.assertEqual(saved.user_id, self.user_a.id)
        self.assertEqual(saved.domain, "food")
        self.assertIsNotNone(saved.created_at)

        # Kiểm tra input_snapshot khớp dữ liệu đầu vào
        self.assertEqual(saved.input_snapshot["budget_max"], 50000)
        self.assertEqual(saved.input_snapshot["meal_type"], "lunch")
        self.assertEqual(saved.input_snapshot["max_prep_time"], 25)
        self.assertEqual(saved.input_snapshot["excluded_ingredients"], ["đậu phộng"])
        self.assertEqual(saved.input_snapshot["preferred_tags"], ["truyền thống"])
        self.assertEqual(saved.input_snapshot["limit"], 5)

        # Kiểm tra result_snapshot khớp kết quả trả về
        self.assertTrue(saved.result_snapshot["success"])
        self.assertEqual(saved.result_snapshot["total"], 2)
        self.assertEqual(len(saved.result_snapshot["items"]), 2)
        self.assertEqual(
            saved.result_snapshot["items"][0]["name"],
            response.items[0].name,
        )

    # ------------------------------------------------------------------
    # Trường hợp 2: Xem danh sách lịch sử
    # ------------------------------------------------------------------
    def test_case_2_list_history_only_returns_current_user_sorted_desc(self) -> None:
        """GET /decisions/history chỉ trả về lịch sử của tài khoản đang đăng nhập, mới nhất trước."""
        authed_a = self._authenticate_with_jwt(self.user_a)
        authed_b = self._authenticate_with_jwt(self.user_b)

        # Tài khoản A thực hiện 2 quyết định
        recommend_decisions(
            payload=DecisionRecommendRequest(budget_max=40000, meal_type="lunch"),
            db=self.db,
            current_user=authed_a,
        )
        recommend_decisions(
            payload=DecisionRecommendRequest(budget_max=60000, meal_type="lunch"),
            db=self.db,
            current_user=authed_a,
        )
        # Tài khoản B thực hiện 1 quyết định
        recommend_decisions(
            payload=DecisionRecommendRequest(budget_max=50000, meal_type="lunch"),
            db=self.db,
            current_user=authed_b,
        )

        # Đặt created_at rõ ràng để kiểm tra thứ tự DESC
        a_decisions = (
            self.db.query(Decision)
            .filter(Decision.user_id == self.user_a.id)
            .order_by(Decision.id.asc())
            .all()
        )
        a_decisions[0].created_at = datetime(2026, 11, 23, 10, 0, 0)
        a_decisions[1].created_at = datetime(2026, 11, 23, 12, 0, 0)
        self.db.commit()

        history_resp = get_decision_history_list(
            limit=20,
            offset=0,
            db=self.db,
            current_user=authed_a,
        )

        self.assertTrue(history_resp.success)
        self.assertEqual(history_resp.total, 2)
        self.assertEqual(len(history_resp.data), 2)
        self.assertEqual(len(history_resp.items), 2)

        # Chỉ có dữ liệu của A, không có của B
        for item in history_resp.data:
            self.assertEqual(item.user_id, self.user_a.id)
            self.assertEqual(item.domain, "food")

        # Sắp xếp created_at DESC (bản ghi 12:00 đứng trước bản ghi 10:00)
        self.assertEqual(history_resp.data[0].id, a_decisions[1].id)
        self.assertEqual(history_resp.data[1].id, a_decisions[0].id)
        self.assertEqual(history_resp.data[0].input_snapshot["budget_max"], 60000)
        self.assertEqual(history_resp.data[1].input_snapshot["budget_max"], 40000)

        # Kiểm tra phân trang limit/offset
        paged_resp = get_decision_history_list(
            limit=1,
            offset=1,
            db=self.db,
            current_user=authed_a,
        )
        self.assertEqual(paged_resp.total, 2)
        self.assertEqual(len(paged_resp.data), 1)
        self.assertEqual(paged_resp.data[0].id, a_decisions[0].id)

    # ------------------------------------------------------------------
    # Trường hợp 3: Xem chi tiết lịch sử
    # ------------------------------------------------------------------
    def test_case_3_get_history_detail_success(self) -> None:
        """GET /decisions/history/{decision_id} trả đúng chi tiết quyết định đã lưu của A."""
        authed_a = self._authenticate_with_jwt(self.user_a)
        payload = DecisionRecommendRequest(
            budget_max=50000,
            meal_type="lunch",
            preferred_tags=["đậm đà"],
            limit=3,
        )
        rec_resp = recommend_decisions(
            payload=payload,
            db=self.db,
            current_user=authed_a,
        )

        saved = (
            self.db.query(Decision)
            .filter(Decision.user_id == self.user_a.id)
            .first()
        )
        self.assertIsNotNone(saved)

        detail_resp = get_decision_history_detail(
            decision_id=saved.id,
            db=self.db,
            current_user=authed_a,
        )

        self.assertTrue(detail_resp.success)
        self.assertEqual(detail_resp.id, saved.id)
        self.assertEqual(detail_resp.data.id, saved.id)
        self.assertEqual(detail_resp.user_id, self.user_a.id)
        self.assertEqual(detail_resp.domain, "food")
        self.assertEqual(detail_resp.input_snapshot["budget_max"], 50000)
        self.assertEqual(
            detail_resp.result_snapshot["total"],
            rec_resp.total,
        )
        self.assertIsNotNone(detail_resp.created_at)

    # ------------------------------------------------------------------
    # Trường hợp 4: Truy cập trái phép (user B xem lịch sử của user A -> 404)
    # ------------------------------------------------------------------
    def test_case_4_unauthorized_access_to_other_user_history_returns_404(self) -> None:
        """Tài khoản A tạo lịch sử; tài khoản B truy cập ID của A -> phải trả về 404."""
        authed_a = self._authenticate_with_jwt(self.user_a)
        authed_b = self._authenticate_with_jwt(self.user_b)

        recommend_decisions(
            payload=DecisionRecommendRequest(budget_max=50000, meal_type="lunch"),
            db=self.db,
            current_user=authed_a,
        )
        decision_a = (
            self.db.query(Decision)
            .filter(Decision.user_id == self.user_a.id)
            .first()
        )
        self.assertIsNotNone(decision_a)

        # Tài khoản B cố truy cập decision_id của A -> phải nhận 404
        with self.assertRaises(ResourceNotFoundException) as ctx_other:
            get_decision_history_detail(
                decision_id=decision_a.id,
                db=self.db,
                current_user=authed_b,
            )
        self.assertEqual(ctx_other.exception.status_code, 404)

        # ID không tồn tại cũng trả về cùng loại 404 để không lộ sự tồn tại của dữ liệu
        with self.assertRaises(ResourceNotFoundException) as ctx_missing:
            get_decision_history_detail(
                decision_id=999999,
                db=self.db,
                current_user=authed_b,
            )
        self.assertEqual(ctx_missing.exception.status_code, 404)
        self.assertEqual(
            ctx_other.exception.error_code,
            ctx_missing.exception.error_code,
        )

    # ------------------------------------------------------------------
    # Trường hợp 5: Không có lịch sử
    # ------------------------------------------------------------------
    def test_case_5_empty_history_returns_empty_list(self) -> None:
        """Người dùng chưa từng recommend -> API danh sách trả về danh sách rỗng, không lỗi."""
        authed_b = self._authenticate_with_jwt(self.user_b)

        history_resp = get_decision_history_list(
            limit=20,
            offset=0,
            db=self.db,
            current_user=authed_b,
        )

        self.assertTrue(history_resp.success)
        self.assertEqual(history_resp.total, 0)
        self.assertEqual(history_resp.data, [])
        self.assertEqual(history_resp.items, [])

    # ------------------------------------------------------------------
    # Trường hợp 6: Chưa đăng nhập hoặc token không hợp lệ -> 401
    # ------------------------------------------------------------------
    def test_case_6_unauthenticated_or_invalid_token_returns_401(self) -> None:
        """Gọi API lịch sử không có token hoặc token sai/hết hạn -> phải trả về 401."""
        # 1. Không có token (credentials=None)
        with self.assertRaises(UnauthorizedException) as ctx_no_token:
            get_current_user(credentials=None, db=self.db)
        self.assertEqual(ctx_no_token.exception.status_code, 401)

        # 2. Token sai định dạng
        bad_creds = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid.jwt.token",
        )
        with self.assertRaises(UnauthorizedException) as ctx_bad_token:
            get_current_user(credentials=bad_creds, db=self.db)
        self.assertEqual(ctx_bad_token.exception.status_code, 401)

        # 3. Token hết hạn
        expired_token = create_access_token(
            user_id=self.user_a.id,
            expires_delta=timedelta(minutes=-5),
        )
        expired_creds = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=expired_token,
        )
        with self.assertRaises(UnauthorizedException) as ctx_expired:
            get_optional_current_user(credentials=expired_creds, db=self.db)
        self.assertEqual(ctx_expired.exception.status_code, 401)

    # ------------------------------------------------------------------
    # Trường hợp 7: Recommend thất bại -> Không tạo bản ghi lịch sử
    # ------------------------------------------------------------------
    def test_case_7_recommend_failure_does_not_create_history(self) -> None:
        """Khi dữ liệu không hợp lệ hoặc lỗi nghiệp vụ -> tuyệt đối không lưu lịch sử."""
        authed_a = self._authenticate_with_jwt(self.user_a)

        # 7a. Dữ liệu đầu vào không hợp lệ (budget_max <= 0 hoặc có thêm user_id giả mạo)
        with self.assertRaises(ValidationError):
            DecisionRecommendRequest(budget_max=-10000)

        with self.assertRaises(ValidationError):
            DecisionRecommendRequest.model_validate(
                {"budget_max": 50000, "user_id": 999}
            )

        self.assertEqual(self.db.query(Decision).count(), 0)

        # 7b. Lỗi nghiệp vụ trong quá trình recommend (cấu hình trọng số trong DB không hợp lệ)
        self.db.query(DecisionCriterion).delete()
        self.db.add(
            DecisionCriterion(
                id=99,
                domain="food",
                name="Giá",
                direction="min",
                weight=Decimal("0.5000"),  # Tổng != 1.0 -> lỗi 400
            )
        )
        self.db.commit()

        with self.assertRaises(DecisionHubException) as ctx_err:
            recommend_decisions(
                payload=DecisionRecommendRequest(budget_max=50000),
                db=self.db,
                current_user=authed_a,
            )
        self.assertEqual(ctx_err.exception.status_code, 400)
        self.assertEqual(self.db.query(Decision).count(), 0)

    def test_transaction_rollback_when_saving_history_fails(self) -> None:
        """Nếu xảy ra lỗi DB khi ghi bảng decisions, transaction phải được rollback."""
        authed_a = self._authenticate_with_jwt(self.user_a)
        payload = DecisionRecommendRequest(budget_max=50000, meal_type="lunch")

        with patch.object(
            self.db,
            "commit",
            side_effect=RuntimeError("Simulated DB commit failure"),
        ):
            with self.assertRaises(DecisionHubException) as ctx:
                recommend_decisions(
                    payload=payload,
                    db=self.db,
                    current_user=authed_a,
                )
            self.assertEqual(ctx.exception.status_code, 500)

        self.assertEqual(self.db.query(Decision).count(), 0)


if __name__ == "__main__":
    unittest.main()
