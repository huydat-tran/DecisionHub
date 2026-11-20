"""Unit tests cho Hard Constraint Filtering và tích hợp vào Decision Engine Pipeline.

Kiểm tra: filters.py (lọc ứng viên) → pipeline.py (thứ tự lọc trước chấm điểm).
"""

from decimal import Decimal
from pathlib import Path
import sys
import unittest

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.modules.decision.engine.filters import filter_candidates, passes_hard_constraints
from app.modules.decision.engine.pipeline import evaluate

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
    name: str,
    price: int,
    meal_type: str = "lunch",
    prep_time: int | None = 15,
    ingredients: list[str] | None = None,
) -> dict:
    return {
        "id": food_id,
        "name": name,
        "price": price,
        "meal_type": meal_type,
        "prep_time": prep_time,
        "ingredients": ingredients if ingredients is not None else [],
        "preference": 80,
    }


class TestFilterCandidates(unittest.TestCase):
    def test_candidate_passing_all_constraints_is_kept(self) -> None:
        candidates = [_food(1, "Món A", 30_000, ingredients=["thịt bò"])]
        kept = filter_candidates(
            candidates,
            budget_max=50_000,
            meal_type="lunch",
            max_prep_time=30,
            excluded_ingredients=["hành"],
        )
        self.assertEqual([c["id"] for c in kept], [1])

    def test_candidate_over_budget_is_removed(self) -> None:
        candidates = [_food(1, "Món A", 60_000)]
        kept = filter_candidates(candidates, budget_max=50_000)
        self.assertEqual(kept, [])

    def test_candidate_with_wrong_meal_type_is_removed(self) -> None:
        candidates = [_food(1, "Món A", 30_000, meal_type="dinner")]
        kept = filter_candidates(candidates, meal_type="lunch")
        self.assertEqual(kept, [])

    def test_candidate_with_excluded_ingredient_is_removed(self) -> None:
        candidates = [_food(1, "Món A", 30_000, ingredients=["Tôm chua"])]
        kept = filter_candidates(candidates, excluded_ingredients=["tôm"])
        self.assertEqual(kept, [])

    def test_candidate_with_prep_time_over_limit_is_removed(self) -> None:
        candidates = [_food(1, "Món A", 30_000, prep_time=45)]
        kept = filter_candidates(candidates, max_prep_time=30)
        self.assertEqual(kept, [])

    def test_candidate_with_prep_time_equal_limit_is_kept(self) -> None:
        candidates = [_food(1, "Món A", 30_000, prep_time=30)]
        kept = filter_candidates(candidates, max_prep_time=30)
        self.assertEqual([c["id"] for c in kept], [1])

    def test_max_prep_time_not_provided_does_not_filter(self) -> None:
        candidates = [_food(1, "Món A", 30_000, prep_time=999)]
        kept = filter_candidates(candidates)
        self.assertEqual([c["id"] for c in kept], [1])

    def test_missing_prep_time_is_removed_when_limit_provided(self) -> None:
        candidates = [_food(1, "Món A", 30_000, prep_time=None)]
        kept = filter_candidates(candidates, max_prep_time=30)
        self.assertEqual(kept, [])

    def test_invalid_prep_time_type_is_removed_without_error(self) -> None:
        candidates = [_food(1, "Món A", 30_000, prep_time="nhanh")]
        kept = filter_candidates(candidates, max_prep_time=30)
        self.assertEqual(kept, [])

    def test_negative_max_prep_time_raises(self) -> None:
        with self.assertRaises(ValueError):
            filter_candidates([_food(1, "Món A", 30_000)], max_prep_time=-1)

    def test_passes_hard_constraints_handles_missing_price(self) -> None:
        candidate = {"id": 1, "name": "Món A"}
        self.assertFalse(passes_hard_constraints(candidate, budget_max=50_000))


class TestFilterCandidatesShortCircuit(unittest.TestCase):
    """filter_candidates() phải dừng ngay khi điều kiện đầu không đạt.

    Nếu không short-circuit, một điều kiện phía sau có `expected` sai kiểu sẽ
    ném ValueError thay vì chỉ loại ứng viên.
    """

    def test_stops_at_first_failing_constraint(self) -> None:
        """Điều kiện đầu fail + điều kiện sau có expected sai kiểu → không raise."""
        candidates = [_food(1, "Món A", 5_000)]
        constraints = {"price": ("<=", 1_000), "prep_time": ("<=", "abc")}
        # Ứng viên đã vi phạm điều kiện price → bị loại, không cần đánh giá prep_time.
        self.assertEqual(filter_candidates(candidates, constraints), [])

    def test_short_circuit_result_matches_explain_variant(self) -> None:
        """Kết quả lọc của filter_candidates() và filter_and_explain_candidates() nhất quán."""
        from app.modules.decision.engine.filters import filter_and_explain_candidates

        candidates = [
            _food(1, "Món A", 5_000),
            _food(2, "Món B", 30_000),
        ]
        constraints = {"price": ("<=", 10_000)}

        kept = filter_candidates(candidates, constraints)
        valid, excluded = filter_and_explain_candidates(candidates, constraints)

        # Cùng tập ứng viên được giữ lại và cùng tập bị loại.
        self.assertEqual([c["id"] for c in kept], [c["id"] for c in valid])
        self.assertEqual([c["id"] for c in kept], [1])
        self.assertEqual(len(excluded), 1)

    def test_explain_variant_evaluates_all_constraints(self) -> None:
        """Bản 'explain' đánh giá MỌI điều kiện để thu thập đủ lý do → lỗi dữ liệu
        ở điều kiện sau vẫn bị nêu ra (khác bản short-circuit)."""
        from app.modules.decision.engine.filters import filter_and_explain_candidates

        candidates = [_food(1, "Món A", 30_000)]
        constraints = {"price": ("<=", 50_000), "prep_time": ("<=", "abc")}

        with self.assertRaises(ValueError):
            filter_and_explain_candidates(candidates, constraints)

    def test_raising_constraint_still_raises_for_passing_candidates(self) -> None:
        """Ứng viên thoả điều kiện đầu vẫn phải đánh giá điều kiện sau → raise nếu sai kiểu."""
        candidates = [_food(1, "Món A", 30_000)]
        constraints = {"price": ("<=", 50_000), "prep_time": ("<=", "abc")}
        with self.assertRaises(ValueError):
            filter_candidates(candidates, constraints)


class TestPipelineIntegratesFiltering(unittest.TestCase):
    def test_filtering_runs_before_scoring(self) -> None:
        """Ứng viên vi phạm ràng buộc không được đưa vào Scoring (điểm không tính lại)."""
        candidates = [
            _food(1, "Món A", 30_000, prep_time=10),
            _food(2, "Món B", 30_000, prep_time=60),
        ]
        results = evaluate(candidates, CRITERIA, domain="food", max_prep_time=30)

        self.assertEqual([r["id"] for r in results], [1])
        # Min-Max chỉ được tính trên tập còn lại: 1 ứng viên → min == max → 100 điểm
        self.assertEqual(results[0]["criteria_scores"]["price"], 100.0)

    def test_all_candidates_removed_returns_empty_list(self) -> None:
        candidates = [_food(1, "Món A", 90_000)]
        results = evaluate(candidates, CRITERIA, domain="food", budget_max=50_000)
        self.assertEqual(results, [])

    def test_empty_candidates_returns_empty_list(self) -> None:
        self.assertEqual(evaluate([], CRITERIA, domain="food"), [])

    def test_evaluate_without_constraints_keeps_all_candidates(self) -> None:
        candidates = [_food(1, "Món A", 90_000, prep_time=999)]
        results = evaluate(candidates, CRITERIA, domain="food")
        self.assertEqual([r["id"] for r in results], [1])

    def test_engine_does_not_import_database(self) -> None:
        """Engine không được phụ thuộc SQLAlchemy/session (không truy vấn DB bên trong)."""
        source = (BACKEND_DIR / "app" / "modules" / "decision" / "engine" / "pipeline.py").read_text(
            encoding="utf-8"
        )
        for forbidden in ("sqlalchemy", "Session", "get_db"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
