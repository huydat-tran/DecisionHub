"""Unit tests cho Bước 2 - Lọc điều kiện bắt buộc (Hard Constraints)."""

from decimal import Decimal
from enum import Enum
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

# Đảm bảo import được `app.*` khi chạy từ root repo hoặc từ `backend/`
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


class MealTypeEnum(Enum):
    SANG = "sang"
    TRUA = "trua"
    TOI = "toi"


class TestHardConstraintBudget(unittest.TestCase):
    def test_budget_max_filters_exceeding_and_keeps_boundary(self) -> None:
        candidates = [
            {"id": 1, "name": "Bánh mì", "price": 25_000},
            {"id": 2, "name": "Phở bò", "price": Decimal("50000")},
            {"id": 3, "name": "Lẩu", "price": 120_000},
        ]
        result = filter_candidates(candidates, budget_max=50_000)
        self.assertEqual([item["id"] for item in result], [1, 2])

    def test_budget_max_excludes_missing_negative_and_invalid_prices(self) -> None:
        candidates = [
            {"id": 1, "name": "Thiếu giá", "price": None},
            {"id": 2, "name": "Giá âm", "price": -10_000},
            {"id": 3, "name": "Bool", "price": True},
            {"id": 4, "name": "NaN", "price": float("nan")},
            {"id": 5, "name": "Inf", "price": float("inf")},
            {"id": 6, "name": "Chuỗi rỗng", "price": ""},
            {"id": 7, "name": "Không phải số", "price": "abc"},
            {"id": 8, "name": "Hợp lệ", "price": "35000"},
        ]
        result = filter_candidates(candidates, budget_max=40_000)
        self.assertEqual([item["id"] for item in result], [8])

    def test_invalid_budget_max_raises_value_error(self) -> None:
        for invalid in (-1, -0.01, float("nan"), float("inf"), True, "abc"):
            with self.subTest(budget_max=invalid):
                with self.assertRaises(ValueError):
                    filter_candidates([{"id": 1, "price": 10_000}], budget_max=invalid)
                with self.assertRaises(ValueError):
                    passes_hard_constraints({"id": 1, "price": 10_000}, budget_max=invalid)


class TestHardConstraintMealType(unittest.TestCase):
    def test_meal_type_matches_case_insensitive_and_enum(self) -> None:
        candidates = [
            {"id": 1, "meal_type": "  Sang  "},
            {"id": 2, "meal_type": MealTypeEnum.TRUA},
            {"id": 3, "meal_type": "toi"},
            {"id": 4, "meal_type": None},
            {"id": 5, "meal_type": ""},
        ]
        self.assertEqual(
            [c["id"] for c in filter_candidates(candidates, meal_type="SANG")],
            [1],
        )
        self.assertEqual(
            [c["id"] for c in filter_candidates(candidates, meal_type=MealTypeEnum.TRUA)],
            [2],
        )


class TestHardConstraintExcludedIngredients(unittest.TestCase):
    def test_excluded_ingredients_supports_str_dict_and_object(self) -> None:
        candidates = [
            {"id": 1, "ingredients": ["Thịt bò", "Hành lá"]},
            {"id": 2, "ingredients": [{"name": "Mắm tôm"}, {"name": "Bún"}]},
            SimpleNamespace(id=3, ingredients=[SimpleNamespace(name="Đậu phộng")]),
            {"id": 4, "ingredients": ["Gà", "Gừng"]},
            {"id": 5, "ingredients": "Tôm sú"},
            {"id": 6, "ingredients": []},
        ]
        result = filter_candidates(
            candidates,
            excluded_ingredients=["  tôm ", "ĐẬU PHỘNG", ""],
        )
        result_ids = [item["id"] if isinstance(item, dict) else item.id for item in result]
        self.assertEqual(result_ids, [1, 4, 6])


class TestHardConstraintsCombined(unittest.TestCase):
    def test_no_compensation_when_any_constraint_fails(self) -> None:
        candidates = [
            {"id": 1, "price": 30_000, "meal_type": "trua", "ingredients": ["Thịt heo"]},
            {"id": 2, "price": 20_000, "meal_type": "sang", "ingredients": ["Thịt heo"]},
            {"id": 3, "price": 20_000, "meal_type": "trua", "ingredients": ["Hành"]},
            {"id": 4, "price": 60_000, "meal_type": "trua", "ingredients": ["Thịt heo"]},
        ]
        result = filter_candidates(
            candidates,
            budget_max=40_000,
            meal_type="trua",
            excluded_ingredients=["hành"],
        )
        self.assertEqual([item["id"] for item in result], [1])

    def test_all_candidates_filtered_returns_empty_list(self) -> None:
        candidates = [
            {"id": 1, "price": 80_000, "meal_type": "trua", "ingredients": []},
        ]
        self.assertEqual(filter_candidates(candidates, budget_max=50_000), [])

    def test_no_constraints_keeps_all_candidates(self) -> None:
        candidates = [{"id": 1}, {"id": 2, "price": None}]
        self.assertEqual(filter_candidates(candidates), candidates)
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


from app.modules.decision.engine.filters import filter_and_explain_candidates
from app.modules.decision.engine.pipeline import evaluate_decision
from app.modules.travel.adapter import adapt_travel_candidates, adapt_travel_criteria
from app.modules.travel.models import TravelPlace, TravelRegion


class TestTravelAdapterConstraintFiltering(unittest.TestCase):
    """Kiểm thử Constraint Filtering sau khi ghép Travel Adapter."""

    def setUp(self) -> None:
        self.places = [
            TravelPlace(
                id=1,
                name="Vịnh Hạ Long",
                province_city="Quảng Ninh",
                region=TravelRegion.BAC,
                estimated_cost=650_000,
                estimated_duration=Decimal("6.5"),
                activity_type="Khám phá thiên nhiên",
                highlights="Thăm hang, Chèo kayak, Ngắm hoàng hôn",
                is_active=True,
            ),
            TravelPlace(
                id=2,
                name="Phố cổ Hội An",
                province_city="Quảng Nam",
                region=TravelRegion.TRUNG,
                estimated_cost=450_000,
                estimated_duration=Decimal("8.0"),
                activity_type="Văn hóa lịch sử",
                highlights="Đèn hoa đăng, Chùa Cầu",
                is_active=True,
            ),
        ]

    def test_adapted_travel_candidates_pass_through_when_no_constraints(self) -> None:
        """Ứng viên Travel qua adapter đi qua filter và pipeline bình thường khi không có constraint."""
        adapted = adapt_travel_candidates(self.places)
        criteria = adapt_travel_criteria()

        kept = filter_candidates(adapted, domain="travel")
        self.assertEqual(kept, adapted)

        valid, excluded = filter_and_explain_candidates(adapted, domain="travel")
        self.assertEqual(len(valid), 2)
        self.assertEqual(excluded, [])

        result = evaluate_decision(adapted, criteria, domain="travel")
        self.assertTrue(result["success"])
        self.assertTrue(result["has_valid_candidates"])
        self.assertEqual(result["total_valid"], 2)
        self.assertEqual(result["total_excluded"], 0)

    def test_travel_domain_active_constraints_currently_raise_value_error(self) -> None:
        """Domain 'travel' chưa đăng ký trong DOMAIN_CONSTRAINT_CONFIG -> truyền constraint phải báo ValueError."""
        adapted = adapt_travel_candidates([self.places[0]])

        with self.assertRaises(ValueError) as ctx1:
            filter_candidates(adapted, {"estimated_cost": ("<=", 1_000_000)}, domain="travel")
        self.assertIn("travel", str(ctx1.exception))

        with self.assertRaises(ValueError) as ctx2:
            filter_and_explain_candidates(
                adapted, {"estimated_duration": ("<=", 5.0)}, domain="travel"
            )
        self.assertIn("travel", str(ctx2.exception))

        with self.assertRaises(ValueError) as ctx3:
            filter_candidates(adapted, budget_max=1_000_000, domain="travel")
        self.assertIn("travel", str(ctx3.exception))

    def test_food_constraints_no_regression_alongside_travel_adapter(self) -> None:
        """Lọc Hard Constraints cho Food vẫn phân tách hợp lệ/bị loại và giải thích đúng."""
        food_candidates = [
            _food(1, "Cơm tấm", price=35_000, meal_type="lunch", prep_time=10, ingredients=["sườn"]),
            _food(2, "Lẩu hải sản", price=120_000, meal_type="lunch", prep_time=25, ingredients=["tôm"]),
            _food(3, "Phở sáng", price=40_000, meal_type="breakfast", prep_time=15, ingredients=["thịt bò"]),
            _food(4, "Mì hầm lâu", price=40_000, meal_type="lunch", prep_time=45, ingredients=["thịt heo"]),
        ]
        valid, excluded = filter_and_explain_candidates(
            food_candidates,
            budget_max=50_000,
            meal_type="lunch",
            max_prep_time=30,
            excluded_ingredients=["tôm"],
        )

        self.assertEqual([c["id"] for c in valid], [1])
        self.assertEqual([e["id"] for e in excluded], [2, 3, 4])
        exc_map = {e["id"]: e for e in excluded}
        self.assertIn("vượt quá ngân sách", exc_map[2]["exclusion_reason"].lower())
        self.assertIn("tôm", exc_map[2]["exclusion_reason"].lower())
        self.assertIn("không phù hợp với bữa ăn yêu cầu", exc_map[3]["exclusion_reason"].lower())
        self.assertIn("vượt quá giới hạn tối đa", exc_map[4]["exclusion_reason"].lower())


if __name__ == "__main__":
    unittest.main()
