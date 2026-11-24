"""Unit tests cho luồng trọng số: Repository → Service → Decision Engine.

Kiểm tra quy ước định danh thống nhất: `field_name` là định danh kỹ thuật chuẩn
của tiêu chí khi dữ liệu đi vào Decision Engine, tên hiển thị trong DB
(vd. "Giá") không được dùng làm key tính toán.
"""

from decimal import Decimal
from pathlib import Path
import sys
import unittest

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.modules.decision.criterion_fields import (
    CANONICAL_FIELD_NAMES,
    resolve_criterion_field,
    resolve_field_name,
)
from app.modules.decision.engine.calculator import calculate_wsm, validate_weights
from app.modules.decision.engine.pipeline import evaluate
from app.modules.decision.models import DecisionCriterion
from app.modules.decision.repository import get_weights_by_domain
from app.modules.decision.service import get_food_weights, get_travel_weights


def _make_session(rows: list[dict]) -> sessionmaker:
    """Tạo session SQLite in-memory với các tiêu chí trong `rows`."""
    engine = create_engine("sqlite://")
    # BigInteger autoincrement không được SQLite hỗ trợ → tạo bảng rồi chèn
    # với `id` tường minh.
    DecisionCriterion.__table__.create(engine)
    session_factory = sessionmaker(bind=engine)
    with session_factory() as db:
        for row in rows:
            db.add(DecisionCriterion(**row))
        db.commit()
    return session_factory


FOOD_ROWS = [
    {"id": 1, "domain": "food", "name": "Giá", "direction": "min", "weight": Decimal("0.4000")},
    {
        "id": 2,
        "domain": "food",
        "name": "Mức phù hợp nhu cầu/khẩu vị",
        "direction": "max",
        "weight": Decimal("0.3500"),
    },
    {
        "id": 3,
        "domain": "food",
        "name": "Thời gian chuẩn bị",
        "direction": "min",
        "weight": Decimal("0.2500"),
    },
]

TRAVEL_ROWS = [
    {"id": 4, "domain": "travel", "name": "cost", "direction": "min", "weight": Decimal("0.4000")},
    {"id": 5, "domain": "travel", "name": "duration", "direction": "min", "weight": Decimal("0.3000")},
    {"id": 6, "domain": "travel", "name": "activities", "direction": "max", "weight": Decimal("0.3000")},
]


class TestCriterionFields(unittest.TestCase):
    """Nguồn định nghĩa duy nhất cho ánh xạ tên tiêu chí → field_name."""

    def test_resolve_display_name_to_field_name(self) -> None:
        self.assertEqual(resolve_field_name("Giá"), "price")
        self.assertEqual(resolve_field_name("Thời gian chuẩn bị"), "prep_time")
        self.assertEqual(resolve_field_name("cost"), "estimated_cost")
        self.assertEqual(resolve_field_name("duration"), "estimated_duration")

    def test_resolve_is_idempotent(self) -> None:
        """field_name đã chuẩn hóa đi qua lại vẫn giữ nguyên."""
        for field_name in CANONICAL_FIELD_NAMES:
            self.assertEqual(resolve_field_name(field_name), field_name)

    def test_unknown_name_raises(self) -> None:
        """Tên không ánh xạ được phải raise, không âm thầm giữ nguyên."""
        with self.assertRaises(ValueError) as ctx:
            resolve_field_name("Hương vị bí mật")
        self.assertIn("Hương vị bí mật", str(ctx.exception))

    def test_criterion_prefers_explicit_field_name(self) -> None:
        criterion = {"name": "Giá", "field_name": "price", "weight": 1.0}
        self.assertEqual(resolve_criterion_field(criterion), "price")

    def test_criterion_with_invalid_explicit_field_name_raises(self) -> None:
        criterion = {"name": "Giá", "field_name": "Giá", "weight": 1.0}
        with self.assertRaises(ValueError):
            resolve_criterion_field(criterion)


class TestRepositoryWeights(unittest.TestCase):
    """Repository trả trọng số theo tên tiêu chí trong DB (giữ vai trò đọc DB)."""

    def test_repository_returns_food_weights_by_db_name(self) -> None:
        session_factory = _make_session(FOOD_ROWS)
        with session_factory() as db:
            weights = get_weights_by_domain(db, domain="food")
        self.assertEqual(
            weights,
            {"Giá": 0.40, "Mức phù hợp nhu cầu/khẩu vị": 0.35, "Thời gian chuẩn bị": 0.25},
        )

    def test_repository_returns_travel_weights_by_db_name(self) -> None:
        session_factory = _make_session(TRAVEL_ROWS)
        with session_factory() as db:
            weights = get_weights_by_domain(db, domain="travel")
        self.assertEqual(weights, {"cost": 0.40, "duration": 0.30, "activities": 0.30})

    def test_repository_falls_back_when_db_empty(self) -> None:
        session_factory = _make_session([])
        with session_factory() as db:
            weights = get_weights_by_domain(db, domain="food")
        self.assertEqual(weights, {"price": 0.40, "preference": 0.35, "prep_time": 0.25})


class TestServiceWeights(unittest.TestCase):
    """Service chuyển đổi cấu hình Repository thành đầu vào cho Engine."""

    def test_service_converts_food_weights_to_field_names(self) -> None:
        session_factory = _make_session(FOOD_ROWS)
        with session_factory() as db:
            weights = get_food_weights(db)

        self.assertEqual(weights, {"price": 0.40, "preference": 0.35, "prep_time": 0.25})
        # Không còn tên hiển thị lọt vào Engine
        self.assertNotIn("Giá", weights)
        self.assertNotIn("Thời gian chuẩn bị", weights)
        for key in weights:
            self.assertIn(key, CANONICAL_FIELD_NAMES)

    def test_service_converts_travel_weights_to_field_names(self) -> None:
        session_factory = _make_session(TRAVEL_ROWS)
        with session_factory() as db:
            weights = get_travel_weights(db)

        self.assertEqual(
            weights,
            {"estimated_cost": 0.40, "estimated_duration": 0.30, "activities": 0.30},
        )
        for key in weights:
            self.assertIn(key, CANONICAL_FIELD_NAMES)

    def test_food_and_travel_use_separate_weight_sets(self) -> None:
        session_factory = _make_session(FOOD_ROWS + TRAVEL_ROWS)
        with session_factory() as db:
            food_weights = get_food_weights(db)
            travel_weights = get_travel_weights(db)

        self.assertNotEqual(food_weights, travel_weights)
        self.assertEqual(set(food_weights) & set(travel_weights), set())

    def test_service_fallback_is_converted_too(self) -> None:
        """Fallback của repository (đã dùng field_name) vẫn qua được bước chuyển đổi."""
        session_factory = _make_session([])
        with session_factory() as db:
            weights = get_food_weights(db)
        self.assertEqual(weights, {"price": 0.40, "preference": 0.35, "prep_time": 0.25})

    def test_service_raises_on_unmapped_criterion(self) -> None:
        rows = FOOD_ROWS + [
            {"id": 9, "domain": "food", "name": "Hương vị", "direction": "max", "weight": Decimal("0.1000")},
        ]
        session_factory = _make_session(rows)
        with session_factory() as db:
            with self.assertRaises(ValueError) as ctx:
                get_food_weights(db)
        self.assertIn("Hương vị", str(ctx.exception))


class TestCalculatorAcceptsFieldNames(unittest.TestCase):
    """Calculator nhận trọng số theo field_name và gắn đúng điểm tương ứng."""

    def test_validate_weights_maps_display_names(self) -> None:
        weights = validate_weights(
            [
                {"name": "Giá", "weight": Decimal("0.4000")},
                {"name": "Mức phù hợp nhu cầu/khẩu vị", "weight": Decimal("0.3500")},
                {"name": "Thời gian chuẩn bị", "weight": Decimal("0.2500")},
            ]
        )
        self.assertEqual(weights, {"price": 0.40, "preference": 0.35, "prep_time": 0.25})

    def test_validate_weights_normalizes_display_name_dict_key(self) -> None:
        """Dict đầu vào dùng key "Giá" được chuẩn hóa thành field_name "price"."""
        weights = validate_weights(
            {"Giá": 0.40, "Mức phù hợp nhu cầu/khẩu vị": 0.35, "Thời gian chuẩn bị": 0.25}
        )
        self.assertEqual(weights, {"price": 0.40, "preference": 0.35, "prep_time": 0.25})

    def test_validate_weights_rejects_unknown_dict_key(self) -> None:
        """Key không ánh xạ được phải bị từ chối, không lọt vào Engine."""
        with self.assertRaises(ValueError) as ctx:
            validate_weights({"Hương vị": 0.5, "price": 0.5})
        self.assertIn("Hương vị", str(ctx.exception))

    def test_validate_weights_still_requires_sum_of_one(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            validate_weights({"price": 0.6, "preference": 0.5})
        self.assertIn("1.0", str(ctx.exception))

    def test_calculate_wsm_uses_weight_by_criteria_scores_key(self) -> None:
        """Trọng số được gắn với đúng key trong criteria_scores."""
        candidates = [
            {
                "id": 1,
                "name": "Món A",
                "criteria_scores": {"price": 40.0, "preference": 100.0, "prep_time": 50.0},
            },
        ]
        weights = validate_weights(
            [
                {"name": "Giá", "weight": 0.40},
                {"name": "Mức phù hợp nhu cầu/khẩu vị", "weight": 0.35},
                {"name": "Thời gian chuẩn bị", "weight": 0.25},
            ]
        )
        results = calculate_wsm(candidates, weights)

        # 0.40*40 + 0.35*100 + 0.25*50 = 16.0 + 35.0 + 12.5 = 63.50
        self.assertEqual(results[0]["score"], 63.50)

    def test_food_and_travel_weights_both_feed_calculate_wsm(self) -> None:
        """Hai bộ trọng số khác nhau dùng chung một calculate_wsm()."""
        food_weights = validate_weights({"price": 0.40, "preference": 0.35, "prep_time": 0.25})
        travel_weights = validate_weights(
            {"estimated_cost": 0.40, "estimated_duration": 0.30, "activities": 0.30}
        )

        food_candidates = [
            {"id": 1, "name": "Món A", "criteria_scores": {"price": 100.0, "preference": 100.0, "prep_time": 100.0}},
        ]
        travel_candidates = [
            {
                "id": 2,
                "name": "Điểm đến",
                "criteria_scores": {
                    "estimated_cost": 100.0,
                    "estimated_duration": 100.0,
                    "activities": 100.0,
                },
            },
        ]

        self.assertEqual(calculate_wsm(food_candidates, food_weights)[0]["score"], 100.0)
        self.assertEqual(calculate_wsm(travel_candidates, travel_weights)[0]["score"], 100.0)

    def test_evaluate_maps_criteria_to_field_names(self) -> None:
        """Pipeline dùng chung field_name giữa scoring và calculator."""
        criteria = [
            {"domain": "food", "name": "Giá", "direction": "min", "weight": Decimal("0.5000")},
            {
                "domain": "food",
                "name": "Mức phù hợp nhu cầu/khẩu vị",
                "direction": "max",
                "weight": Decimal("0.5000"),
            },
        ]
        candidates = [
            {"id": 1, "name": "Món A", "price": 20_000, "preference": 80},
            {"id": 2, "name": "Món B", "price": 40_000, "preference": 80},
        ]
        results = evaluate(candidates, criteria, domain="food")

        self.assertEqual(set(results[0]["criteria_scores"]), {"price", "preference"})
        self.assertEqual(results[0]["name"], "Món A")


if __name__ == "__main__":
    unittest.main()
