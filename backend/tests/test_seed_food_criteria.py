"""Unit tests kiểm tra seed tiêu chí Food mặc định trong `backend/sql/seeds/decision_criteria.sql`."""

from decimal import Decimal
from pathlib import Path
import sys
import unittest

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import Engine, create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.modules.decision.engine.calculator import validate_weights
from app.modules.decision.engine.pipeline import evaluate_decision
from app.modules.decision.models import DecisionCriterion
from app.modules.decision.repository import get_criteria_by_domain, get_food_criteria
from app.modules.decision.service import get_food_weights

FOOD_DOMAIN = "food"
SQL_SEED_PATH = BACKEND_DIR / "sql" / "seeds" / "decision_criteria.sql"

EXPECTED_FOOD_ROWS = (
    ("food", "Giá", "min", Decimal("0.4000")),
    ("food", "Mức phù hợp nhu cầu/khẩu vị", "max", Decimal("0.3500")),
    ("food", "Thời gian chuẩn bị", "min", Decimal("0.2500")),
)

EXPECTED_TRAVEL_ROWS = (
    ("travel", "cost", "min", Decimal("0.4000")),
    ("travel", "duration", "min", Decimal("0.3000")),
    ("travel", "activities", "max", Decimal("0.3000")),
)


def _create_sqlite_criteria_session() -> tuple[Engine, sessionmaker[Session]]:
    """Tạo SQLite in-memory với bảng `decision_criteria` khớp MySQL/Alembic."""
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        # SQLite chỉ tự tăng khóa khi cột là INTEGER PRIMARY KEY; MySQL dùng
        # BIGINT AUTO_INCREMENT và seed không truyền id.
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
    return engine, sessionmaker(bind=engine, autoflush=False, autocommit=False)


def _quantize_weight(value: Decimal) -> Decimal:
    return Decimal(value).quantize(Decimal("0.0001"))


def _sql_seed_statements() -> list[str]:
    """Tách các câu lệnh INSERT thực thi được từ `decision_criteria.sql`."""
    statements: list[str] = []
    for chunk in SQL_SEED_PATH.read_text(encoding="utf-8").split(";"):
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


def _apply_sql_seed(engine: Engine) -> None:
    """Thực thi toàn bộ câu lệnh seed từ `decision_criteria.sql`."""
    statements = _sql_seed_statements()
    with engine.begin() as conn:
        for stmt in statements:
            conn.exec_driver_sql(stmt)


class TestFoodCriteriaSqlSeed(unittest.TestCase):
    def setUp(self) -> None:
        self.engine, self.SessionLocal = _create_sqlite_criteria_session()
        self.db: Session = self.SessionLocal()

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    def test_sql_seed_file_exists_and_has_required_header(self) -> None:
        self.assertTrue(SQL_SEED_PATH.is_file())
        raw_sql = SQL_SEED_PATH.read_text(encoding="utf-8")
        self.assertIn("SET NAMES utf8mb4;", raw_sql)
        self.assertIn("USE decision_hub;", raw_sql)
        statements = _sql_seed_statements()
        self.assertEqual(len(statements), 6)

    def test_sql_seed_inserts_three_default_food_criteria(self) -> None:
        _apply_sql_seed(self.engine)

        rows = sorted(get_food_criteria(self.db), key=lambda r: r.id)
        self.assertEqual(
            [
                (r.domain, r.name, r.direction, _quantize_weight(r.weight))
                for r in rows
            ],
            list(EXPECTED_FOOD_ROWS),
        )
        for row in rows:
            self.assertIn(row.direction, ("min", "max"))
            self.assertGreaterEqual(_quantize_weight(row.weight), Decimal("0"))
            self.assertLessEqual(_quantize_weight(row.weight), Decimal("1"))

        total_weight = sum((_quantize_weight(r.weight) for r in rows), Decimal("0"))
        self.assertEqual(total_weight, Decimal("1.0000"))

        self.assertEqual(
            validate_weights(rows),
            {"price": 0.40, "preference": 0.35, "prep_time": 0.25},
        )
        self.assertEqual(
            get_food_weights(self.db),
            {"price": 0.40, "preference": 0.35, "prep_time": 0.25},
        )

    def test_sql_seed_is_idempotent_and_preserves_existing_food_weight(self) -> None:
        _apply_sql_seed(self.engine)
        _apply_sql_seed(self.engine)

        self.assertEqual(len(get_criteria_by_domain(self.db, domain=FOOD_DOMAIN)), 3)
        self.assertEqual(len(get_criteria_by_domain(self.db, domain="travel")), 3)

        price_row = self.db.scalar(
            select(DecisionCriterion).where(
                DecisionCriterion.domain == FOOD_DOMAIN,
                DecisionCriterion.name == "Giá",
            )
        )
        assert price_row is not None
        price_row.weight = Decimal("0.5000")
        self.db.commit()

        _apply_sql_seed(self.engine)

        self.db.expire_all()
        refreshed = self.db.scalar(
            select(DecisionCriterion).where(
                DecisionCriterion.domain == FOOD_DOMAIN,
                DecisionCriterion.name == "Giá",
            )
        )
        assert refreshed is not None
        self.assertEqual(_quantize_weight(refreshed.weight), Decimal("0.5000"))

    def test_sql_seed_inserts_only_missing_food_criteria_on_partial_db(self) -> None:
        self.db.add(
            DecisionCriterion(
                domain=FOOD_DOMAIN,
                name="Giá",
                direction="min",
                weight=Decimal("0.4000"),
            )
        )
        self.db.commit()

        _apply_sql_seed(self.engine)

        self.db.expire_all()
        rows = sorted(get_food_criteria(self.db), key=lambda r: r.id)
        self.assertEqual(len(rows), 3)
        self.assertEqual(
            [
                (r.domain, r.name, r.direction, _quantize_weight(r.weight))
                for r in rows
            ],
            list(EXPECTED_FOOD_ROWS),
        )

    def test_sql_seed_keeps_food_and_travel_domains_separate(self) -> None:
        _apply_sql_seed(self.engine)

        food_rows = sorted(
            get_criteria_by_domain(self.db, domain=FOOD_DOMAIN),
            key=lambda r: r.id,
        )
        travel_rows = sorted(
            get_criteria_by_domain(self.db, domain="travel"),
            key=lambda r: r.id,
        )

        self.assertEqual(
            [
                (r.domain, r.name, r.direction, _quantize_weight(r.weight))
                for r in food_rows
            ],
            list(EXPECTED_FOOD_ROWS),
        )
        self.assertEqual(
            [
                (r.domain, r.name, r.direction, _quantize_weight(r.weight))
                for r in travel_rows
            ],
            list(EXPECTED_TRAVEL_ROWS),
        )
        self.assertEqual(
            sum((_quantize_weight(r.weight) for r in food_rows), Decimal("0")),
            Decimal("1.0000"),
        )
        self.assertEqual(
            sum((_quantize_weight(r.weight) for r in travel_rows), Decimal("0")),
            Decimal("1.0000"),
        )

    def test_sql_seeded_food_criteria_work_with_decision_engine(self) -> None:
        _apply_sql_seed(self.engine)
        criteria = get_food_criteria(self.db)

        candidates = [
            {
                "id": 1,
                "name": "Phở bò tái",
                "price": 45000,
                "meal_type": "breakfast",
                "prep_time": 15,
                "tags": ["truyền thống", "nóng"],
                "ingredients": ["Thịt bò", "Bánh phở"],
            },
            {
                "id": 2,
                "name": "Bánh mì thịt",
                "price": 25000,
                "meal_type": "breakfast",
                "prep_time": 5,
                "tags": ["nhanh", "khô"],
                "ingredients": ["Bánh mì", "Thịt nguội"],
            },
        ]

        eval_result = evaluate_decision(
            candidates=candidates,
            criteria=criteria,
            domain=FOOD_DOMAIN,
            user_preferences=["nhanh"],
            limit=5,
        )

        self.assertTrue(eval_result["has_valid_candidates"])
        self.assertEqual(eval_result["total_valid"], 2)
        ranked = eval_result["valid_candidates"]
        self.assertEqual([item["rank"] for item in ranked], [1, 2])
        self.assertEqual(ranked[0]["name"], "Bánh mì thịt")
        for item in ranked:
            self.assertEqual(
                set(item["criteria_scores"]),
                {"price", "preference", "prep_time"},
            )


if __name__ == "__main__":
    unittest.main()
