"""Unit tests cho chuẩn hóa Candidate giữa Scoring và Ranking.

Kiểm tra việc chuyển đổi ứng viên (dict / Pydantic / SQLAlchemy ORM) về dict phẳng,
để Ranking đọc được `id`/`name`/`price`... ở cấp ngoài cùng.
"""

from decimal import Decimal
from pathlib import Path
import sys
import unittest

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from pydantic import BaseModel
from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.modules.decision.engine.calculator import calculate_wsm
from app.modules.decision.engine.pipeline import evaluate
from app.modules.decision.engine.ranking import rank_candidates
from app.modules.decision.engine.scoring import score_candidates


class _Base(DeclarativeBase):
    pass


class _FoodORM(_Base):
    """Bản rút gọn của bảng `foods` (chỉ các cột liên quan tới tie-break)."""

    __tablename__ = "_test_foods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    price: Mapped[Decimal] = mapped_column(Integer)
    meal_type: Mapped[str] = mapped_column(String(50))
    prep_time: Mapped[int | None] = mapped_column(Integer, nullable=True)


class _TravelORM(_Base):
    """Bản rút gọn của bảng `travel_places` (dùng `estimated_cost` làm chi phí)."""

    __tablename__ = "_test_travel_places"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    estimated_cost: Mapped[int] = mapped_column(Integer)
    estimated_duration: Mapped[Decimal] = mapped_column(Integer)


class _FoodPydantic(BaseModel):
    """Pydantic model mô phỏng schema đầu ra của module food."""

    id: int
    name: str
    price: int
    meal_type: str
    prep_time: int | None = None


CRITERIA = [
    {"domain": "food", "name": "Giá", "direction": "min", "weight": Decimal("0.5000")},
    {
        "domain": "food",
        "name": "Mức phù hợp nhu cầu/khẩu vị",
        "direction": "max",
        "weight": Decimal("0.5000"),
    },
]


class TestCandidateConversion(unittest.TestCase):
    def test_dict_candidate_keeps_top_level_fields(self) -> None:
        """Dict ứng viên giữ nguyên các trường ở cấp ngoài cùng."""
        candidates = [{"id": 1, "name": "Phở bò", "price": 40_000, "preference": 80}]
        scored = score_candidates(candidates, CRITERIA)

        self.assertEqual(scored[0]["id"], 1)
        self.assertEqual(scored[0]["name"], "Phở bò")
        self.assertEqual(scored[0]["price"], 40_000)
        self.assertIn("criteria_scores", scored[0])

    def test_orm_candidate_is_flattened(self) -> None:
        """ORM object được chuyển về dict phẳng, không bọc trong `item`."""
        candidates = [
            _FoodORM(id=1, name="Phở bò", price=40_000, meal_type="lunch", prep_time=10),
            _FoodORM(id=2, name="Bún chả", price=20_000, meal_type="lunch", prep_time=20),
        ]
        scored = score_candidates(candidates, CRITERIA)

        self.assertEqual(scored[0]["id"], 1)
        self.assertEqual(scored[0]["name"], "Phở bò")
        self.assertEqual(scored[0]["price"], 40_000)
        self.assertEqual(scored[0]["meal_type"], "lunch")
        self.assertEqual(scored[0]["prep_time"], 10)
        # Ứng viên gốc vẫn truy cập được qua `item`
        self.assertIs(scored[0]["item"], candidates[0])
        # Không lộ thuộc tính nội bộ của SQLAlchemy
        self.assertNotIn("_sa_instance_state", scored[0])

    def test_pydantic_candidate_is_flattened(self) -> None:
        """Pydantic model được chuyển về dict phẳng."""
        candidates = [
            _FoodPydantic(id=1, name="Phở bò", price=40_000, meal_type="lunch", prep_time=10),
        ]
        scored = score_candidates(candidates, CRITERIA)

        self.assertEqual(scored[0]["id"], 1)
        self.assertEqual(scored[0]["name"], "Phở bò")
        self.assertEqual(scored[0]["price"], 40_000)
        self.assertIs(scored[0]["item"], candidates[0])

    def test_travel_orm_uses_estimated_cost(self) -> None:
        """Travel dùng `estimated_cost` — Ranking phải đọc được trường này."""
        travel_criteria = [
            {"domain": "travel", "name": "cost", "direction": "min", "weight": Decimal("1.0000")},
        ]
        candidates = [
            _TravelORM(id=1, name="Hạ Long", estimated_cost=900, estimated_duration=1),
            _TravelORM(id=2, name="Sapa", estimated_cost=300, estimated_duration=1),
        ]
        scored = score_candidates(candidates, travel_criteria)

        self.assertEqual(scored[0]["estimated_cost"], 900)
        self.assertEqual(scored[1]["estimated_cost"], 300)

    def test_orm_candidate_not_mutated(self) -> None:
        """Ứng viên ORM gốc không bị gắn thêm thuộc tính nào."""
        food = _FoodORM(id=1, name="Phở bò", price=40_000, meal_type="lunch", prep_time=10)
        before = dict(food.__dict__)

        score_candidates([food], CRITERIA)

        self.assertEqual(food.__dict__, before)
        self.assertFalse(hasattr(food, "criteria_scores"))

    def test_dict_candidate_not_mutated(self) -> None:
        """Dict ứng viên gốc không bị thêm `criteria_scores`."""
        candidate = {"id": 1, "name": "Phở bò", "price": 40_000, "preference": 80}
        score_candidates([candidate], CRITERIA)

        self.assertNotIn("criteria_scores", candidate)


class TestRankingReadsFlattenedFields(unittest.TestCase):
    def test_ranking_tie_break_uses_orm_name_and_cost(self) -> None:
        """Hai ứng viên ORM bằng điểm → tie-break theo price, không phải sentinel."""
        candidates = [
            _FoodORM(id=1, name="Bún chả", price=60_000, meal_type="lunch", prep_time=10),
            _FoodORM(id=2, name="Phở bò", price=20_000, meal_type="lunch", prep_time=10),
        ]
        scored = score_candidates(candidates, CRITERIA)
        calculated = calculate_wsm(scored, CRITERIA)
        ranked = rank_candidates(calculated)

        # Điểm bằng nhau (min=max → 100 cho mọi tiêu chí) → tie-break cost
        self.assertEqual([r["name"] for r in ranked], ["Phở bò", "Bún chả"])
        self.assertEqual([r["rank"] for r in ranked], [1, 2])

    def test_ranking_tie_break_uses_orm_id(self) -> None:
        """Bằng điểm, bằng chi phí, bằng tên → sắp theo ID tăng dần."""
        candidates = [
            _FoodORM(id=9, name="Món X", price=30_000, meal_type="lunch", prep_time=10),
            _FoodORM(id=2, name="Món X", price=30_000, meal_type="lunch", prep_time=10),
        ]
        scored = score_candidates(candidates, CRITERIA)
        calculated = calculate_wsm(scored, CRITERIA)
        ranked = rank_candidates(calculated)

        self.assertEqual([r["id"] for r in ranked], [2, 9])

    def test_criteria_scores_and_score_survive_pipeline(self) -> None:
        """`criteria_scores` không mất, `score` được thêm sau khi tính WSM."""
        candidates = [
            _FoodORM(id=1, name="Phở bò", price=40_000, meal_type="lunch", prep_time=10),
        ]
        results = evaluate(candidates, CRITERIA, domain="food")

        self.assertIn("criteria_scores", results[0])
        self.assertIn("score", results[0])
        self.assertEqual(results[0]["name"], "Phở bò")
        self.assertEqual(results[0]["id"], 1)
        self.assertEqual(results[0]["rank"], 1)


if __name__ == "__main__":
    unittest.main()
