"""Unit tests cho cơ chế lọc ứng viên dựa trên cấu hình HardConstraint từ Database.

Phủ 4 tầng:
- Repository: đọc cấu hình hard_constraints theo domain, chỉ lấy bản ghi active.
- Service: kết hợp cấu hình DB với giá trị request → cấu hình cho Engine.
- Filtering: thực thi 6 operator trên 4 field của Food.
- Pipeline: Filtering chạy trước Scoring, không còn ứng viên → trả [].
"""

from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
import sys
import unittest

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.modules.decision.engine.filters import filter_candidates, passes_hard_constraints
from app.modules.decision.engine.pipeline import evaluate
from app.modules.decision.hard_constraint_fields import (
    DOMAIN_CONSTRAINT_CONFIG,
    SUPPORTED_OPERATORS,
    get_default_operators,
    get_domain_constraint_config,
    get_request_field_mapping,
    get_supported_fields,
    validate_constraint,
)
from app.modules.decision.models import DecisionCriterion, HardConstraint
from app.modules.decision.repository import get_hard_constraints_by_domain, get_weights_by_domain
from app.modules.decision.service import build_constraints, build_food_constraints

CRITERIA = [
    {"domain": "food", "name": "Giá", "direction": "min", "weight": Decimal("0.5000")},
    {
        "domain": "food",
        "name": "Mức phù hợp nhu cầu/khẩu vị",
        "direction": "max",
        "weight": Decimal("0.5000"),
    },
]


def _food(
    food_id: int,
    name: str = "Món A",
    price: int | None = 30_000,
    meal_type: str | None = "lunch",
    prep_time: int | None = 15,
    ingredients: list[str] | None = None,
) -> dict:
    return {
        "id": food_id,
        "name": name,
        "price": price,
        "meal_type": meal_type,
        "prep_time": prep_time,
        "ingredients": [] if ingredients is None else ingredients,
        "preference": 80,
    }


def _make_session(rows: list[dict]) -> sessionmaker:
    """Tạo session SQLite in-memory với các hard constraint trong `rows`."""
    engine = create_engine("sqlite://")
    # BigInteger autoincrement không được SQLite hỗ trợ → tạo bảng rồi chèn
    # với `id` tường minh.
    HardConstraint.__table__.create(engine)
    DecisionCriterion.__table__.create(engine)
    session_factory = sessionmaker(bind=engine)
    with session_factory() as db:
        for row in rows:
            db.add(HardConstraint(**row))
        db.commit()
    return session_factory


FOOD_CONSTRAINT_ROWS = [
    {
        "id": 1,
        "domain": "food",
        "name": "Ngân sách tối đa",
        "field_name": "price",
        "operator": "<=",
        "is_active": True,
    },
    {
        "id": 2,
        "domain": "food",
        "name": "Loại bữa ăn",
        "field_name": "meal_type",
        "operator": "=",
        "is_active": True,
    },
    {
        "id": 3,
        "domain": "food",
        "name": "Thời gian chuẩn bị tối đa",
        "field_name": "prep_time",
        "operator": "<=",
        "is_active": True,
    },
    {
        "id": 4,
        "domain": "food",
        "name": "Nguyên liệu cần tránh",
        "field_name": "ingredients",
        "operator": "not_in",
        "is_active": True,
    },
]


class TestHardConstraintFields(unittest.TestCase):
    """Nguồn định nghĩa duy nhất cho field/operator của HardConstraint, theo domain."""

    def test_food_config_is_registered(self) -> None:
        config = get_domain_constraint_config("food")
        self.assertEqual(
            config["fields"],
            {
                "price": "number",
                "meal_type": "text",
                "prep_time": "number",
                "ingredients": "list",
            },
        )

    def test_supported_fields_and_operators(self) -> None:
        self.assertEqual(
            get_supported_fields("food"),
            {"price", "meal_type", "prep_time", "ingredients"},
        )
        self.assertEqual(SUPPORTED_OPERATORS, {"<=", ">=", "=", "!=", "in", "not_in"})

    def test_request_field_mapping_is_centralized(self) -> None:
        self.assertEqual(
            get_request_field_mapping("food"),
            {
                "budget_max": "price",
                "meal_type": "meal_type",
                "max_prep_time": "prep_time",
                "excluded_ingredients": "ingredients",
            },
        )

    def test_default_operators_unchanged(self) -> None:
        self.assertEqual(
            get_default_operators("food"),
            {
                "price": "<=",
                "meal_type": "=",
                "prep_time": "<=",
                "ingredients": "not_in",
            },
        )

    def test_unknown_domain_raises_clear_error(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            get_domain_constraint_config("travel")
        self.assertIn("travel", str(ctx.exception))

    def test_config_has_no_food_specific_global_leak(self) -> None:
        """Không còn biến global kiểu Food-only gây nhầm lẫn khi thêm domain."""
        for domain, config in DOMAIN_CONSTRAINT_CONFIG.items():
            self.assertEqual(set(config), {"fields", "request_mapping", "default_operators"})
            self.assertTrue(config["fields"], domain)
            # Mọi field trong mapping/default_operators phải là field hợp lệ.
            for field_name in config["request_mapping"].values():
                self.assertIn(field_name, config["fields"], domain)
            for field_name in config["default_operators"]:
                self.assertIn(field_name, config["fields"], domain)

    def test_validate_accepts_valid_config(self) -> None:
        validate_constraint("food", "price", "<=", "Ngân sách tối đa")

    def test_validate_rejects_unknown_field(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            validate_constraint("food", "flavor", "<=", "Sai field")
        self.assertIn("flavor", str(ctx.exception))

    def test_validate_rejects_unknown_operator(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            validate_constraint("food", "price", "<", "Sai operator")
        self.assertIn("<", str(ctx.exception))

    def test_validate_rejects_operator_not_applicable_to_field(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            validate_constraint("food", "meal_type", "<=", "Sai tổ hợp")
        self.assertIn("meal_type", str(ctx.exception))

    def test_validate_rejects_unknown_domain(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            validate_constraint("travel", "price", "<=")
        self.assertIn("travel", str(ctx.exception))

    def test_validate_accepts_all_six_operators_on_number_field(self) -> None:
        for operator in ("<=", ">=", "=", "!=", "in", "not_in"):
            validate_constraint("food", "price", operator)

    def test_hard_constraint_fields_does_not_import_database(self) -> None:
        source = (
            BACKEND_DIR / "app" / "modules" / "decision" / "hard_constraint_fields.py"
        ).read_text(encoding="utf-8")
        for forbidden in ("sqlalchemy", "Session", "get_db", "repository"):
            self.assertNotIn(forbidden, source)


class TestRepositoryHardConstraints(unittest.TestCase):
    """Repository đọc cấu hình hard_constraints, chỉ lấy bản ghi active."""

    def test_returns_active_constraints_of_domain(self) -> None:
        rows = FOOD_CONSTRAINT_ROWS + [
            {
                "id": 5,
                "domain": "travel",
                "name": "Chi phí tối đa",
                "field_name": "estimated_cost",
                "operator": "<=",
                "is_active": True,
            }
        ]
        session_factory = _make_session(rows)
        with session_factory() as db:
            configs = get_hard_constraints_by_domain(db, domain="food")

        self.assertEqual(
            configs,
            [
                {"name": "Ngân sách tối đa", "field_name": "price", "operator": "<="},
                {"name": "Loại bữa ăn", "field_name": "meal_type", "operator": "="},
                {
                    "name": "Thời gian chuẩn bị tối đa",
                    "field_name": "prep_time",
                    "operator": "<=",
                },
                {
                    "name": "Nguyên liệu cần tránh",
                    "field_name": "ingredients",
                    "operator": "not_in",
                },
            ],
        )

    def test_inactive_constraints_are_excluded(self) -> None:
        rows = [
            {**FOOD_CONSTRAINT_ROWS[0], "id": 1, "is_active": False},
            FOOD_CONSTRAINT_ROWS[1],
        ]
        session_factory = _make_session(rows)
        with session_factory() as db:
            configs = get_hard_constraints_by_domain(db, domain="food")

        self.assertEqual(
            configs,
            [{"name": "Loại bữa ăn", "field_name": "meal_type", "operator": "="}],
        )

    def test_empty_result_when_domain_has_no_config(self) -> None:
        session_factory = _make_session([])
        with session_factory() as db:
            self.assertEqual(get_hard_constraints_by_domain(db, domain="food"), [])

    def test_get_weights_by_domain_contract_unchanged(self) -> None:
        """Hàm trọng số không bị ảnh hưởng bởi thay đổi này."""
        session_factory = _make_session([])
        with session_factory() as db:
            weights = get_weights_by_domain(db, domain="food")
        self.assertEqual(weights, {"price": 0.40, "preference": 0.35, "prep_time": 0.25})


class TestServiceBuildConstraints(unittest.TestCase):
    """Service kết hợp cấu hình DB với giá trị request."""

    def test_maps_request_values_to_constraint_fields(self) -> None:
        session_factory = _make_session(FOOD_CONSTRAINT_ROWS)
        with session_factory() as db:
            constraints = build_food_constraints(
                db,
                budget_max=100_000,
                meal_type="lunch",
                max_prep_time=30,
                excluded_ingredients=["peanut", "shrimp"],
            )

        self.assertEqual(
            constraints,
            {
                "price": ("<=", 100_000),
                "meal_type": ("=", "lunch"),
                "prep_time": ("<=", 30),
                "ingredients": ("not_in", ["peanut", "shrimp"]),
            },
        )

    def test_operator_comes_from_database(self) -> None:
        rows = [
            {
                "id": 1,
                "domain": "food",
                "name": "Ngân sách tối đa",
                "field_name": "price",
                "operator": ">=",
                "is_active": True,
            }
        ]
        session_factory = _make_session(rows)
        with session_factory() as db:
            constraints = build_food_constraints(db, budget_max=100_000)

        self.assertEqual(constraints, {"price": (">=", 100_000)})

    def test_none_values_are_skipped(self) -> None:
        session_factory = _make_session(FOOD_CONSTRAINT_ROWS)
        with session_factory() as db:
            constraints = build_food_constraints(db, budget_max=100_000, meal_type=None)

        self.assertEqual(constraints, {"price": ("<=", 100_000)})

    def test_empty_list_value_is_skipped(self) -> None:
        session_factory = _make_session(FOOD_CONSTRAINT_ROWS)
        with session_factory() as db:
            constraints = build_food_constraints(db, excluded_ingredients=[])

        self.assertEqual(constraints, {})

    def test_warns_when_request_value_has_no_active_config(self) -> None:
        """Request có giá trị nhưng DB không có cấu hình active → cảnh báo, không áp dụng."""
        rows = [FOOD_CONSTRAINT_ROWS[0]]
        session_factory = _make_session(rows)
        with session_factory() as db:
            with self.assertLogs("app.modules.decision.service", level="WARNING") as logs:
                constraints = build_food_constraints(db, budget_max=100_000, max_prep_time=30)

        self.assertEqual(constraints, {"price": ("<=", 100_000)})
        self.assertTrue(any("max_prep_time" in line for line in logs.output))

    def test_raises_on_invalid_field_in_database_config(self) -> None:
        rows = [
            {
                "id": 1,
                "domain": "food",
                "name": "Hương vị",
                "field_name": "flavor",
                "operator": "=",
                "is_active": True,
            }
        ]
        session_factory = _make_session(rows)
        with session_factory() as db:
            with self.assertRaises(ValueError) as ctx:
                build_food_constraints(db, budget_max=100_000)

        self.assertIn("flavor", str(ctx.exception))

    def test_raises_on_invalid_operator_in_database_config(self) -> None:
        invalid = [
            {
                "name": "Ngân sách tối đa",
                "field_name": "price",
                "operator": "<",
            }
        ]
        with patch(
            "app.modules.decision.service.get_hard_constraints_by_domain",
            return_value=invalid,
        ):
            with self.assertRaises(ValueError) as ctx:
                build_constraints(
                    None,  # type: ignore[arg-type]
                    domain="food",
                    request_values={"budget_max": 100_000},
                )

        self.assertIn("operator", str(ctx.exception))

    def test_raises_on_domain_without_constraint_config(self) -> None:
        with patch(
            "app.modules.decision.service.get_hard_constraints_by_domain",
            return_value=[],
        ):
            with self.assertRaises(ValueError) as ctx:
                build_constraints(
                    None,  # type: ignore[arg-type]
                    domain="travel",
                    request_values={"budget_max": 100_000},
                )

        self.assertIn("travel", str(ctx.exception))


class TestFilterOperators(unittest.TestCase):
    """Đủ 6 operator trên 4 field của Food."""

    def test_numeric_operators(self) -> None:
        candidate = _food(1, price=30_000, prep_time=15)

        self.assertTrue(passes_hard_constraints(candidate, {"price": ("<=", 30_000)}))
        self.assertTrue(passes_hard_constraints(candidate, {"price": ("<=", 40_000)}))
        self.assertFalse(passes_hard_constraints(candidate, {"price": ("<=", 20_000)}))
        self.assertTrue(passes_hard_constraints(candidate, {"price": (">=", 30_000)}))
        self.assertFalse(passes_hard_constraints(candidate, {"price": (">=", 40_000)}))
        self.assertTrue(passes_hard_constraints(candidate, {"price": ("=", 30_000)}))
        self.assertFalse(passes_hard_constraints(candidate, {"price": ("=", 20_000)}))
        self.assertTrue(passes_hard_constraints(candidate, {"price": ("!=", 20_000)}))
        self.assertFalse(passes_hard_constraints(candidate, {"price": ("!=", 30_000)}))
        self.assertTrue(passes_hard_constraints(candidate, {"price": ("in", [20_000, 30_000])}))
        self.assertFalse(passes_hard_constraints(candidate, {"price": ("in", [20_000])}))
        self.assertTrue(passes_hard_constraints(candidate, {"price": ("not_in", [20_000])}))
        self.assertFalse(passes_hard_constraints(candidate, {"price": ("not_in", [30_000])}))

    def test_text_operators(self) -> None:
        candidate = _food(1, meal_type="lunch")

        self.assertTrue(passes_hard_constraints(candidate, {"meal_type": ("=", "lunch")}))
        self.assertTrue(passes_hard_constraints(candidate, {"meal_type": ("=", "Lunch")}))
        self.assertFalse(passes_hard_constraints(candidate, {"meal_type": ("=", "dinner")}))
        self.assertTrue(passes_hard_constraints(candidate, {"meal_type": ("!=", "dinner")}))
        self.assertFalse(passes_hard_constraints(candidate, {"meal_type": ("!=", "lunch")}))
        self.assertTrue(
            passes_hard_constraints(candidate, {"meal_type": ("in", ["lunch", "dinner"])})
        )
        self.assertFalse(passes_hard_constraints(candidate, {"meal_type": ("in", ["dinner"])}))
        self.assertTrue(passes_hard_constraints(candidate, {"meal_type": ("not_in", ["dinner"])}))
        self.assertFalse(passes_hard_constraints(candidate, {"meal_type": ("not_in", ["lunch"])}))

    def test_ingredients_operators(self) -> None:
        candidate = _food(1, ingredients=["thịt bò", "hành"])

        self.assertTrue(
            passes_hard_constraints(candidate, {"ingredients": ("not_in", ["tôm", "peanut"])})
        )
        self.assertFalse(
            passes_hard_constraints(candidate, {"ingredients": ("not_in", ["hành"])})
        )
        self.assertTrue(
            passes_hard_constraints(candidate, {"ingredients": ("in", ["thịt bò", "hành"])})
        )
        self.assertFalse(
            passes_hard_constraints(candidate, {"ingredients": ("in", ["thịt bò"])})
        )


class TestFilterFieldRules(unittest.TestCase):
    """Quy tắc xử lý theo từng field Food."""

    def test_multiple_constraints_applied_together(self) -> None:
        candidates = [
            _food(1, "Món A", price=30_000, meal_type="lunch", prep_time=10),
            _food(2, "Món B", price=90_000, meal_type="lunch", prep_time=10),
            _food(3, "Món C", price=30_000, meal_type="dinner", prep_time=10),
            _food(4, "Món D", price=30_000, meal_type="lunch", prep_time=60),
        ]
        kept = filter_candidates(
            candidates,
            {
                "price": ("<=", 50_000),
                "meal_type": ("=", "lunch"),
                "prep_time": ("<=", 30),
            },
        )
        self.assertEqual([c["id"] for c in kept], [1])

    def test_missing_numeric_field_is_removed(self) -> None:
        candidate = {"id": 1, "name": "Món A"}
        self.assertFalse(passes_hard_constraints(candidate, {"price": ("<=", 50_000)}))
        self.assertFalse(passes_hard_constraints(candidate, {"prep_time": ("<=", 30)}))

    def test_missing_meal_type_is_removed(self) -> None:
        candidate = {"id": 1, "name": "Món A"}
        self.assertFalse(passes_hard_constraints(candidate, {"meal_type": ("=", "lunch")}))

    def test_missing_ingredients_are_removed_when_constraint_applies(self) -> None:
        candidate = {"id": 1, "name": "Món A"}
        self.assertFalse(
            passes_hard_constraints(candidate, {"ingredients": ("not_in", ["tôm"])})
        )

    def test_invalid_numeric_value_is_removed_without_error(self) -> None:
        candidate = _food(1, prep_time="nhanh")
        self.assertFalse(passes_hard_constraints(candidate, {"prep_time": ("<=", 30)}))

    def test_invalid_meal_type_value_is_removed_without_error(self) -> None:
        candidate = _food(1, meal_type="")
        self.assertFalse(passes_hard_constraints(candidate, {"meal_type": ("=", "lunch")}))

    def test_invalid_ingredients_type_is_removed_without_error(self) -> None:
        candidate = _food(1)
        candidate["ingredients"] = "thịt bò"  # chuỗi thay vì danh sách
        self.assertFalse(
            passes_hard_constraints(candidate, {"ingredients": ("not_in", ["tôm"])})
        )

    def test_empty_constraints_keeps_all_candidates(self) -> None:
        candidates = [_food(1, price=90_000, prep_time=999)]
        self.assertEqual(len(filter_candidates(candidates, {})), 1)
        self.assertEqual(len(filter_candidates(candidates)), 1)

    def test_invalid_constraint_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            filter_candidates([_food(1)], {"price": ("<", 1000)})
        with self.assertRaises(ValueError):
            filter_candidates([_food(1)], {"flavor": ("=", "x")})


class TestLegacyParametersStillWork(unittest.TestCase):
    """Các caller cũ dùng tham số rời vẫn hoạt động qua cùng cơ chế constraints."""

    def test_legacy_filter_parameters(self) -> None:
        candidates = [_food(1, price=30_000, prep_time=15, ingredients=["thịt bò"])]
        kept = filter_candidates(
            candidates,
            budget_max=50_000,
            meal_type="lunch",
            max_prep_time=30,
            excluded_ingredients=["hành"],
        )
        self.assertEqual([c["id"] for c in kept], [1])

    def test_legacy_negative_value_raises(self) -> None:
        with self.assertRaises(ValueError):
            filter_candidates([_food(1)], max_prep_time=-1)
        with self.assertRaises(ValueError):
            filter_candidates([_food(1)], budget_max=-1)

    def test_legacy_non_numeric_value_does_not_raise_type_error(self) -> None:
        """Giá trị không phải số không được gây TypeError khi kiểm tra âm."""
        with self.assertRaises(ValueError) as ctx:
            filter_candidates([_food(1)], max_prep_time="nhanh")
        self.assertNotIsInstance(ctx.exception, TypeError)

    def test_filters_module_has_no_database_dependency(self) -> None:
        source = (
            BACKEND_DIR / "app" / "modules" / "decision" / "engine" / "filters.py"
        ).read_text(encoding="utf-8")
        for forbidden in ("sqlalchemy", "Session", "get_db", "repository"):
            self.assertNotIn(forbidden, source)


class TestDomainAwareFiltering(unittest.TestCase):
    """Filtering dùng cấu hình theo domain, cơ chế lọc vẫn dùng chung."""

    def test_food_domain_filtering_unchanged(self) -> None:
        candidates = [_food(1, price=30_000, meal_type="lunch", prep_time=15)]
        kept = filter_candidates(
            candidates,
            {"price": ("<=", 50_000), "meal_type": ("=", "lunch")},
            domain="food",
        )
        self.assertEqual([c["id"] for c in kept], [1])

    def test_legacy_parameters_use_domain_default_operators(self) -> None:
        candidates = [_food(1, price=30_000)]
        kept = filter_candidates(candidates, budget_max=50_000, domain="food")
        self.assertEqual([c["id"] for c in kept], [1])

    def test_unknown_domain_raises_clear_error(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            filter_candidates([_food(1)], {"price": ("<=", 1000)}, domain="travel")
        self.assertIn("travel", str(ctx.exception))

    def test_field_outside_domain_config_is_rejected(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            filter_candidates([_food(1)], {"flavor": ("=", "x")}, domain="food")
        self.assertIn("flavor", str(ctx.exception))


class TestPipelineWithConstraints(unittest.TestCase):
    """Pipeline nhận `constraints` và vẫn lọc trước Scoring."""

    def test_filtering_runs_before_scoring(self) -> None:
        candidates = [
            _food(1, "Món A", price=30_000, prep_time=10),
            _food(2, "Món B", price=30_000, prep_time=60),
        ]
        results = evaluate(
            candidates,
            CRITERIA,
            domain="food",
            constraints={"prep_time": ("<=", 30)},
        )
        self.assertEqual([r["id"] for r in results], [1])
        # Min-Max chỉ tính trên tập còn lại: 1 ứng viên → min == max → 100 điểm
        self.assertEqual(results[0]["criteria_scores"]["price"], 100.0)

    def test_removed_candidate_is_not_scored(self) -> None:
        candidates = [_food(1, "Món A", price=90_000, prep_time=10)]
        results = evaluate(
            candidates,
            CRITERIA,
            domain="food",
            constraints={"price": ("<=", 50_000)},
        )
        self.assertEqual(results, [])

    def test_no_candidate_after_filtering_returns_empty_list(self) -> None:
        candidates = [_food(1, "Món A", price=90_000)]
        results = evaluate(
            candidates,
            CRITERIA,
            domain="food",
            constraints={"price": ("<=", 50_000)},
        )
        self.assertEqual(results, [])

    def test_legacy_caller_still_works(self) -> None:
        candidates = [_food(1, "Món A", price=30_000, prep_time=10)]
        results = evaluate(candidates, CRITERIA, domain="food", max_prep_time=30)
        self.assertEqual([r["id"] for r in results], [1])


if __name__ == "__main__":
    unittest.main()
