"""Unit and integration tests for Decision Service and POST /decisions/food/recommend."""

import sys
import unittest
from decimal import Decimal
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.common.exceptions import DecisionHubException
from app.core.database import Base
from app.modules.decision.decision_response import DecisionResponse
from app.modules.decision.models import DecisionCriterion, HardConstraint
from app.modules.decision.repository import (
    get_criteria_by_domain,
    get_food_candidates,
    get_hard_constraints_by_domain,
    get_weights_by_domain,
)
from app.modules.decision.router import recommend_decisions
from app.modules.decision.schema import DecisionRecommendRequest
from app.modules.decision.service import (
    _build_food_reasons,
    _format_vnd,
    _normalize_food_tags,
    recommend_food,
)
from app.modules.food.models_food import Food, FoodIngredient, Ingredient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


class TestDecisionService(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine, autoflush=False, autocommit=False)

    @classmethod
    def tearDownClass(cls) -> None:
        Base.metadata.drop_all(bind=cls.engine)

    def setUp(self) -> None:
        self.db: Session = self.SessionLocal()
        # Clean up tables
        self.db.query(FoodIngredient).delete()
        self.db.query(Food).delete()
        self.db.query(Ingredient).delete()
        self.db.query(DecisionCriterion).delete()
        self.db.query(HardConstraint).delete()
        self.db.commit()

        # Seed standard criteria for food (total = 1.0)
        self.criteria = [
            DecisionCriterion(id=1, domain="food", name="Giá", direction="min", weight=Decimal("0.4000")),
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
        self.db.add_all(self.criteria)

        # Seed standard hard constraints for food
        self.constraints = [
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
        self.db.add_all(self.constraints)

        # Seed standard ingredients
        self.ing_bo = Ingredient(id=1, name="Thịt bò")
        self.ing_pho = Ingredient(id=2, name="Bánh phở")
        self.ing_dau = Ingredient(id=3, name="Đậu phộng")
        self.ing_heo = Ingredient(id=4, name="Thịt heo nướng")
        self.ing_bun = Ingredient(id=5, name="Bún tươi")
        self.db.add_all([self.ing_bo, self.ing_pho, self.ing_dau, self.ing_heo, self.ing_bun])
        self.db.commit()

        # Seed standard foods
        self.food_pho = Food(
            id=1,
            name="Phở bò tái",
            price=Decimal("45000.00"),
            meal_type="breakfast",
            prep_time=15,
            tags=["nước", "truyền thống"],
            is_active=True,
        )
        self.food_pho.ingredients = [self.ing_bo, self.ing_pho]

        self.food_buncha = Food(
            id=2,
            name="Bún chả Hà Nội",
            price=Decimal("35000.00"),
            meal_type="lunch",
            prep_time=20,
            tags=["đậm đà", "truyền thống"],
            is_active=True,
        )
        self.food_buncha.ingredients = [self.ing_heo, self.ing_bun]

        self.food_banhmi = Food(
            id=3,
            name="Bánh mì kẹp",
            price=Decimal("20000.00"),
            meal_type="breakfast",
            prep_time=5,
            tags=["nhanh", "giòn"],
            is_active=True,
        )
        self.food_banhmi.ingredients = [self.ing_dau]

        self.db.add_all([self.food_pho, self.food_buncha, self.food_banhmi])
        self.db.commit()

    def tearDown(self) -> None:
        self.db.rollback()
        self.db.close()

    def test_repository_get_candidates_and_criteria(self) -> None:
        """Kiểm tra repository lấy danh sách món ăn và tiêu chí từ database."""
        candidates = get_food_candidates(self.db)
        self.assertEqual(len(candidates), 3)
        self.assertTrue(all(hasattr(c, "ingredients") for c in candidates))

        criteria = get_criteria_by_domain(self.db, domain="food")
        self.assertEqual(len(criteria), 3)

        weights = get_weights_by_domain(self.db, domain="food")
        self.assertEqual(len(weights), 3)

        constraints = get_hard_constraints_by_domain(self.db, domain="food")
        self.assertEqual(len(constraints), 4)

    def test_recommend_food_successful_flow(self) -> None:
        """Đề xuất thành công với đầy đủ thông tin: id, name, price, score, rank, criteria_scores."""
        req = DecisionRecommendRequest(
            budget_max=50000,
            preferred_tags=["truyền thống"],
            limit=5,
        )
        resp: DecisionResponse = recommend_food(self.db, req)

        self.assertIsInstance(resp, DecisionResponse)
        self.assertEqual(resp.total, 3)
        self.assertEqual(len(resp.items), 3)
        self.assertEqual(resp.limit, 5)

        # Kiểm tra phần tử đầu tiên
        top_item = resp.items[0]
        self.assertIsNotNone(top_item.id)
        self.assertEqual(top_item.id, top_item.food_id)
        self.assertIsNotNone(top_item.name)
        self.assertGreater(top_item.price, 0)
        self.assertGreaterEqual(top_item.score, 0.0)
        self.assertLessEqual(top_item.score, 100.0)
        self.assertEqual(top_item.rank, 1)

        # Kiểm tra criteria_scores
        self.assertIsNotNone(top_item.criteria_scores.price)
        self.assertIsNotNone(top_item.criteria_scores.preference)
        self.assertIsNotNone(top_item.criteria_scores.prep_time)

        # Kiểm tra thứ hạng rank tăng dần
        ranks = [item.rank for item in resp.items]
        self.assertEqual(ranks, [1, 2, 3])

        # Kiểm tra điểm số giảm dần
        scores = [item.score for item in resp.items]
        self.assertTrue(scores[0] >= scores[1] >= scores[2])

        # Kiểm tra có ít nhất 1 lý do hợp lý
        self.assertTrue(len(top_item.reasons) >= 1)

    def test_recommend_food_budget_constraint_filtering(self) -> None:
        """Món ăn vượt quá ngân sách (budget_max) phải bị loại trừ."""
        # Ngân sách 30.000đ: Phở (45k) và Bún chả (35k) bị loại, chỉ còn Bánh mì (20k)
        req = DecisionRecommendRequest(
            budget_max=30000,
            limit=5,
        )
        resp: DecisionResponse = recommend_food(self.db, req)
        self.assertEqual(resp.total, 1)
        self.assertEqual(len(resp.items), 1)
        self.assertEqual(resp.items[0].name, "Bánh mì kẹp")
        self.assertEqual(resp.items[0].price, 20000)

    def test_recommend_food_excluded_ingredients_filtering(self) -> None:
        """Món ăn chứa nguyên liệu cần tránh (excluded_ingredients) phải bị loại trừ."""
        # Tránh 'thịt bò' -> Phở bò tái bị loại
        req = DecisionRecommendRequest(
            budget_max=50000,
            excluded_ingredients=["thịt bò"],
            limit=5,
        )
        resp: DecisionResponse = recommend_food(self.db, req)
        item_names = [item.name for item in resp.items]
        self.assertNotIn("Phở bò tái", item_names)
        self.assertIn("Bún chả Hà Nội", item_names)
        self.assertIn("Bánh mì kẹp", item_names)

    def test_recommend_food_meal_type_filtering(self) -> None:
        """Lọc theo meal_type chính xác."""
        req = DecisionRecommendRequest(
            budget_max=50000,
            meal_type="lunch",
            limit=5,
        )
        resp: DecisionResponse = recommend_food(self.db, req)
        self.assertEqual(resp.total, 1)
        self.assertEqual(resp.items[0].name, "Bún chả Hà Nội")

    def test_recommend_food_empty_result_contract(self) -> None:
        """Khi không có món ăn nào thỏa mãn, trả về danh sách rỗng đúng contract."""
        # Ngân sách 10.000đ (thấp hơn mọi món)
        req = DecisionRecommendRequest(
            budget_max=10000,
            limit=5,
        )
        resp: DecisionResponse = recommend_food(self.db, req)
        self.assertEqual(resp.total, 0)
        self.assertEqual(len(resp.items), 0)
        self.assertEqual(resp.applied_filters.budget_max, 10000)

    def test_recommend_food_empty_database(self) -> None:
        """Khi database không có món ăn nào, trả về danh sách rỗng."""
        self.db.query(FoodIngredient).delete()
        self.db.query(Food).delete()
        self.db.commit()

        req = DecisionRecommendRequest(budget_max=50000)
        resp: DecisionResponse = recommend_food(self.db, req)
        self.assertEqual(resp.total, 0)
        self.assertEqual(resp.items, [])

    def test_recommend_food_invalid_weights_sum_raises_exception(self) -> None:
        """Khi tổng trọng số trong database khác 1.0, phải raise DecisionHubException."""
        self.db.query(DecisionCriterion).delete()
        # Thêm trọng số có tổng = 0.8 (không bằng 1.0)
        invalid_criteria = [
            DecisionCriterion(id=10, domain="food", name="Giá", direction="min", weight=Decimal("0.5000")),
            DecisionCriterion(
                id=11,
                domain="food",
                name="Thời gian chuẩn bị",
                direction="min",
                weight=Decimal("0.3000"),
            ),
        ]
        self.db.add_all(invalid_criteria)
        self.db.commit()

        req = DecisionRecommendRequest(budget_max=50000)
        with self.assertRaises(DecisionHubException) as ctx:
            recommend_food(self.db, req)
        self.assertIn("1.0", ctx.exception.message)

    def test_recommend_food_invalid_constraint_config_raises_exception(self) -> None:
        """Khi bảng hard_constraints có cấu hình operator không tương thích với kiểu field, phải raise DecisionHubException."""
        self.db.query(HardConstraint).delete()
        invalid_constraint = HardConstraint(
            id=20,
            domain="food",
            name="Toán tử không hợp lệ cho nguyên liệu",
            field_name="ingredients",
            operator="<=",  # DB check constraint cho phép <=, nhưng hard_constraint_fields chỉ cho phép in/not_in
            is_active=True,
        )
        self.db.add(invalid_constraint)
        self.db.commit()

        req = DecisionRecommendRequest(budget_max=50000)
        with self.assertRaises(DecisionHubException) as ctx:
            recommend_food(self.db, req)
        self.assertIn("không hợp lệ", ctx.exception.message)

    def test_helpers(self) -> None:
        """Kiểm tra các hàm helper format, tags và reasons."""
        self.assertEqual(_format_vnd(35000), "35.000đ")
        self.assertEqual(_normalize_food_tags(["cay", "nóng"]), ["cay", "nóng"])
        self.assertEqual(_normalize_food_tags("chay, thanh đạm"), ["chay", "thanh đạm"])
        self.assertEqual(_normalize_food_tags(None), [])

        reasons = _build_food_reasons(
            price_int=35000,
            budget_max=50000,
            prep_time=15,
            max_prep_time=20,
            meal_type="lunch",
            matched_tags=["đậm đà"],
        )
        self.assertEqual(len(reasons), 3)
        self.assertIn("35.000đ", reasons[0])
        self.assertIn("đậm đà", reasons[1])
        self.assertIn("15 phút", reasons[2])

    def test_recommend_endpoint_e2e(self) -> None:
        """Kiểm tra gọi trực tiếp hàm xử lý của router recommend_decisions."""
        req = DecisionRecommendRequest(
            budget_max=50000,
            preferred_tags=["truyền thống"],
            limit=5,
        )
        resp = recommend_decisions(payload=req, db=self.db)
        self.assertEqual(resp.total, 3)
        self.assertEqual(len(resp.items), 3)
        self.assertEqual(resp.items[0].rank, 1)
        self.assertGreater(resp.items[0].score, 0)
        self.assertIsNotNone(resp.items[0].criteria_scores)

        # Test với giới hạn ngân sách
        req_budget = DecisionRecommendRequest(
            budget_max=25000,
            limit=5,
        )
        resp_budget = recommend_decisions(payload=req_budget, db=self.db)
        self.assertEqual(resp_budget.total, 1)
        self.assertEqual(resp_budget.items[0].name, "Bánh mì kẹp")


if __name__ == "__main__":
    unittest.main()
