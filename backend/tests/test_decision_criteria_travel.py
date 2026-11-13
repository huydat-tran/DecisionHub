"""Kiểm tra criteria Travel và pipeline WSM dùng chung với Food."""

from decimal import Decimal
from pathlib import Path
import unittest

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.modules.decision.engine.pipeline import evaluate
from app.modules.decision.models import DecisionCriterion, HardConstraint
from app.modules.decision.repository import list_criteria_by_domain

SEED_PATH = Path(__file__).resolve().parents[1] / "sql" / "seeds" / "decision_criteria.sql"

FOOD_CRITERIA = (
    ("Giá", "min", Decimal("0.4000")),
    ("Mức phù hợp nhu cầu/khẩu vị", "max", Decimal("0.3500")),
    ("Thời gian chuẩn bị", "min", Decimal("0.2500")),
)
TRAVEL_CRITERIA = (
    ("cost", "min", Decimal("0.4000")),
    ("duration", "min", Decimal("0.3000")),
    ("activities", "max", Decimal("0.3000")),
)


def _seed_statements() -> list[str]:
    statements: list[str] = []
    for chunk in SEED_PATH.read_text(encoding="utf-8").split(";"):
        lines = [
            line
            for line in chunk.splitlines()
            if line.strip() and not line.strip().startswith("--")
        ]
        statement = "\n".join(lines).strip()
        if not statement:
            continue
        upper = statement.upper()
        if upper.startswith("SET ") or upper.startswith("USE "):
            continue
        statements.append(statement)
    return statements


def _weight(value: Decimal) -> Decimal:
    return Decimal(value).quantize(Decimal("0.0001"))


class CriteriaAndPipelineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite://")
        with self.engine.begin() as connection:
            # SQLite chỉ tự tăng khóa khi cột là INTEGER PRIMARY KEY.
            # MySQL dùng BIGINT AUTO_INCREMENT; seed không ghi id.
            connection.exec_driver_sql(
                """
                CREATE TABLE decision_criteria (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain VARCHAR(20) NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    direction VARCHAR(10) NOT NULL,
                    weight NUMERIC(5, 4) NOT NULL,
                    CONSTRAINT uq_decision_criteria_domain_name UNIQUE (domain, name),
                    CONSTRAINT ck_decision_criteria_domain CHECK (domain IN ('food', 'travel')),
                    CONSTRAINT ck_decision_criteria_direction CHECK (direction IN ('min', 'max')),
                    CONSTRAINT ck_decision_criteria_weight CHECK (weight >= 0 AND weight <= 1)
                )
                """
            )
            connection.exec_driver_sql(
                """
                CREATE TABLE hard_constraints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain VARCHAR(20) NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    field_name VARCHAR(50) NOT NULL,
                    operator VARCHAR(20) NOT NULL,
                    description VARCHAR(255),
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    CONSTRAINT uq_hard_constraints_domain_name UNIQUE (domain, name),
                    CONSTRAINT ck_hard_constraints_domain CHECK (domain IN ('food', 'travel')),
                    CONSTRAINT ck_hard_constraints_operator
                        CHECK (operator IN ('<=', '>=', '=', '!=', 'in', 'not_in'))
                )
                """
            )
        self.Session = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)

    def tearDown(self) -> None:
        self.engine.dispose()

    def _apply_seed(self) -> None:
        with self.engine.begin() as connection:
            for statement in _seed_statements():
                connection.exec_driver_sql(statement)

    def _rows(self, domain: str) -> list[DecisionCriterion]:
        db = self.Session()
        try:
            return list_criteria_by_domain(db, domain)
        finally:
            db.close()

    def test_food_and_travel_criteria_are_loaded_separately(self) -> None:
        self._apply_seed()

        food = self._rows("food")
        travel = self._rows("travel")

        self.assertEqual(
            [(row.name, row.direction, _weight(row.weight)) for row in food],
            list(FOOD_CRITERIA),
        )
        self.assertEqual(
            [(row.name, row.direction, _weight(row.weight)) for row in travel],
            list(TRAVEL_CRITERIA),
        )
        self.assertTrue({"cost", "duration", "activities"} <= {row.name for row in travel})

    def test_travel_directions_weights_and_food_unchanged(self) -> None:
        self._apply_seed()
        travel = self._rows("travel")
        directions = {row.name: row.direction for row in travel}
        weights = {row.name: _weight(row.weight) for row in travel}

        self.assertEqual(directions["cost"], "min")
        self.assertEqual(directions["duration"], "min")
        self.assertEqual(directions["activities"], "max")
        self.assertEqual(sum(weights.values(), Decimal("0")), Decimal("1.0000"))
        for weight in weights.values():
            self.assertGreaterEqual(weight, Decimal("0"))
            self.assertLessEqual(weight, Decimal("1"))

        food = self._rows("food")
        self.assertEqual(
            [(row.name, row.direction, _weight(row.weight)) for row in food],
            list(FOOD_CRITERIA),
        )

    def test_weight_and_direction_constraints(self) -> None:
        db = self.Session()
        try:
            db.add(
                DecisionCriterion(
                    domain="travel",
                    name="too_heavy",
                    direction="min",
                    weight=Decimal("1.5000"),
                )
            )
            with self.assertRaises(IntegrityError) as heavy:
                db.commit()
            self.assertIn("ck_decision_criteria_weight", str(heavy.exception))
            db.rollback()

            db.add(
                DecisionCriterion(
                    domain="travel",
                    name="negative",
                    direction="min",
                    weight=Decimal("-0.1000"),
                )
            )
            with self.assertRaises(IntegrityError) as negative:
                db.commit()
            self.assertIn("ck_decision_criteria_weight", str(negative.exception))
            db.rollback()

            db.add(
                DecisionCriterion(
                    domain="travel",
                    name="bad_direction",
                    direction="avg",
                    weight=Decimal("0.1000"),
                )
            )
            with self.assertRaises(IntegrityError) as direction:
                db.commit()
            self.assertIn("ck_decision_criteria_direction", str(direction.exception))
        finally:
            db.close()

    def test_seed_is_idempotent(self) -> None:
        self._apply_seed()
        self._apply_seed()
        self.assertEqual(len(self._rows("food")), 3)
        self.assertEqual(len(self._rows("travel")), 3)
        self.assertEqual(len(self._rows("food")) + len(self._rows("travel")), 6)

    def test_engine_scores_only_the_requested_domain(self) -> None:
        self._apply_seed()
        criteria = self._rows("food") + self._rows("travel")
        candidates = [
            {
                "id": 1,
                "name": "Hội An",
                "tie_cost": 100,
                "values": {
                    "cost": 100,
                    "duration": 1,
                    "activities": 0,
                    "Giá": 100,
                    "Mức phù hợp nhu cầu/khẩu vị": 0,
                    "Thời gian chuẩn bị": 10,
                },
            },
            {
                "id": 2,
                "name": "Sa Pa",
                "tie_cost": 200,
                "values": {
                    "cost": 200,
                    "duration": 3,
                    "activities": 100,
                    "Giá": 200,
                    "Mức phù hợp nhu cầu/khẩu vị": 100,
                    "Thời gian chuẩn bị": 10,
                },
            },
        ]

        ranked = evaluate(candidates, criteria, "travel")

        self.assertEqual([item["name"] for item in ranked], ["Hội An", "Sa Pa"])
        self.assertEqual(ranked[0]["rank"], 1)
        self.assertEqual(ranked[1]["rank"], 2)
        self.assertEqual(set(ranked[0]["criteria_scores"]), {"cost", "duration", "activities"})
        self.assertEqual(ranked[0]["score"], 70.0)
        self.assertEqual(ranked[0]["criteria_scores"]["cost"], 100.0)
        self.assertEqual(ranked[0]["criteria_scores"]["duration"], 100.0)
        self.assertEqual(ranked[0]["criteria_scores"]["activities"], 0.0)
        self.assertEqual(ranked[1]["score"], 30.0)
        self.assertEqual(ranked[1]["criteria_scores"]["cost"], 0.0)
        self.assertEqual(ranked[1]["criteria_scores"]["activities"], 100.0)

        food_ranked = evaluate(candidates, criteria, "food")
        self.assertEqual(
            set(food_ranked[0]["criteria_scores"]),
            {"Giá", "Mức phù hợp nhu cầu/khẩu vị", "Thời gian chuẩn bị"},
        )
        self.assertNotIn("cost", food_ranked[0]["criteria_scores"])

    def test_min_and_max_follow_stored_direction(self) -> None:
        candidates = [
            {"id": 1, "name": "Ngắn", "values": {"duration": 2}},
            {"id": 2, "name": "Dài", "values": {"duration": 8}},
        ]
        shorter_better = [
            DecisionCriterion(
                domain="travel",
                name="duration",
                direction="min",
                weight=Decimal("1"),
            )
        ]
        longer_better = [
            DecisionCriterion(
                domain="travel",
                name="duration",
                direction="max",
                weight=Decimal("1"),
            )
        ]

        min_ranked = evaluate(candidates, shorter_better, "travel")
        max_ranked = evaluate(candidates, longer_better, "travel")

        self.assertEqual(min_ranked[0]["name"], "Ngắn")
        self.assertEqual(min_ranked[0]["criteria_scores"]["duration"], 100.0)
        self.assertEqual(min_ranked[1]["criteria_scores"]["duration"], 0.0)
        self.assertEqual(max_ranked[0]["name"], "Dài")
        self.assertEqual(max_ranked[0]["criteria_scores"]["duration"], 100.0)
        self.assertEqual(max_ranked[1]["criteria_scores"]["duration"], 0.0)

    def test_equal_values_normalize_to_100_and_tie_breaks_by_cost_then_name(self) -> None:
        criteria = [
            DecisionCriterion(
                domain="travel",
                name="cost",
                direction="min",
                weight=Decimal("1"),
            )
        ]
        same_score = evaluate(
            [
                {"id": 2, "name": "Beta", "tie_cost": 90, "values": {"cost": 150}},
                {"id": 1, "name": "Alpha", "tie_cost": 90, "values": {"cost": 150}},
            ],
            criteria,
            "travel",
        )
        self.assertEqual(same_score[0]["score"], 100.0)
        self.assertEqual(same_score[1]["score"], 100.0)
        self.assertEqual([item["name"] for item in same_score], ["Alpha", "Beta"])

        lower_cost_first = evaluate(
            [
                {"id": 1, "name": "Đắt hơn", "tie_cost": 300, "values": {"cost": 150}},
                {"id": 2, "name": "Rẻ hơn", "tie_cost": 100, "values": {"cost": 150}},
            ],
            criteria,
            "travel",
        )
        self.assertEqual([item["name"] for item in lower_cost_first], ["Rẻ hơn", "Đắt hơn"])

    def test_hard_constraint_accepts_travel_domain(self) -> None:
        db = self.Session()
        try:
            db.add(
                HardConstraint(
                    domain="travel",
                    name="Ngân sách tối đa",
                    field_name="estimated_cost",
                    operator="<=",
                    description="Kiểm tra domain travel dùng được cấu hình hiện có",
                    is_active=True,
                )
            )
            db.commit()
            stored = db.query(HardConstraint).one()
            self.assertEqual(stored.domain, "travel")
            self.assertTrue(stored.is_active)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
