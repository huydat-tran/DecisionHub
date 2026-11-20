"""Unit tests cho Food Preference Scoring (khớp tag người dùng với tag món ăn).

Kiểm tra hàm `score_preference()` và việc tích hợp vào `score_candidates()` /
pipeline WSM mà không ảnh hưởng `price` và `prep_time`.
"""

from decimal import Decimal
from pathlib import Path
import sys
import unittest

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.modules.decision.engine.pipeline import evaluate
from app.modules.decision.engine.scoring import (
    NEUTRAL_PREFERENCE_SCORE,
    score_candidates,
    score_preference,
)

USER_PREFERENCES = ["high_protein", "low_oil", "non_spicy"]


class TestScorePreferenceBasic(unittest.TestCase):
    """Trường hợp cơ bản: toàn bộ / một phần / không sở thích nào khớp."""

    def test_all_preferences_match_returns_one(self) -> None:
        tags = ["high_protein", "low_oil", "non_spicy"]
        self.assertEqual(score_preference(tags, USER_PREFERENCES), 1.0)

    def test_partial_match_returns_ratio(self) -> None:
        tags = ["high_protein", "low_oil"]
        self.assertAlmostEqual(score_preference(tags, USER_PREFERENCES), 2 / 3)

    def test_no_match_returns_zero(self) -> None:
        tags = ["spicy", "high_fat"]
        self.assertEqual(score_preference(tags, USER_PREFERENCES), 0.0)

    def test_extra_candidate_tags_do_not_affect_score(self) -> None:
        """Tag của món không nằm trong sở thích không tính vào tử số."""
        tags = ["high_protein", "low_oil", "non_spicy", "cheese"]
        self.assertEqual(score_preference(tags, USER_PREFERENCES), 1.0)


class TestScorePreferenceEdgeCases(unittest.TestCase):
    """Dữ liệu đặc biệt: thiếu tags, rỗng, trùng lặp, hoa/thường, khoảng trắng, sai kiểu."""

    def test_candidate_without_tags_field_returns_zero(self) -> None:
        self.assertEqual(score_preference(None, USER_PREFERENCES), 0.0)

    def test_candidate_with_empty_tags_returns_zero(self) -> None:
        self.assertEqual(score_preference([], USER_PREFERENCES), 0.0)

    def test_candidate_with_blank_tags_returns_zero(self) -> None:
        self.assertEqual(score_preference(["", "   "], USER_PREFERENCES), 0.0)

    def test_user_preferences_empty_returns_neutral(self) -> None:
        self.assertEqual(score_preference(["high_protein"], []), NEUTRAL_PREFERENCE_SCORE)

    def test_user_preferences_none_returns_neutral(self) -> None:
        self.assertEqual(score_preference(["high_protein"], None), NEUTRAL_PREFERENCE_SCORE)

    def test_user_preferences_only_blank_returns_neutral(self) -> None:
        self.assertEqual(score_preference(["high_protein"], ["", "  "]), NEUTRAL_PREFERENCE_SCORE)

    def test_duplicate_tags_counted_once(self) -> None:
        """Tag trùng lặp chỉ tính một lần ở cả phía ứng viên lẫn phía sở thích."""
        tags = ["high_protein", "high_protein", "low_oil"]
        self.assertAlmostEqual(score_preference(tags, USER_PREFERENCES), 2 / 3)

        # Sở thích trùng lặp cũng được loại trùng: 2 sở thích duy nhất, khớp cả 2.
        duplicated_prefs = ["high_protein", "high_protein", "low_oil"]
        self.assertAlmostEqual(score_preference(tags, duplicated_prefs), 1.0)

    def test_case_insensitive_match(self) -> None:
        tags = ["HIGH_PROTEIN", "Low_Oil"]
        self.assertAlmostEqual(score_preference(tags, USER_PREFERENCES), 2 / 3)

    def test_whitespace_is_trimmed(self) -> None:
        tags = ["  high_protein  ", "low_oil\t"]
        self.assertAlmostEqual(score_preference(tags, USER_PREFERENCES), 2 / 3)

    def test_no_substring_matching(self) -> None:
        """'spicy' không được coi là khớp 'non_spicy' (không so khớp substring)."""
        self.assertEqual(score_preference(["spicy"], ["non_spicy"]), 0.0)

    def test_invalid_types_are_handled_gracefully(self) -> None:
        """Sai kiểu dữ liệu không gây lỗi và không nâng điểm."""
        self.assertEqual(score_preference(123, USER_PREFERENCES), 0.0)
        self.assertEqual(score_preference({"a": 1}, USER_PREFERENCES), 0.0)
        self.assertEqual(score_preference(["high_protein"], 123), NEUTRAL_PREFERENCE_SCORE)

    def test_score_always_within_zero_one(self) -> None:
        for tags in ([], ["high_protein"], ["spicy"], ["high_protein", "low_oil", "non_spicy"]):
            score = score_preference(tags, USER_PREFERENCES)
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)


class TestPreferenceInScoreCandidates(unittest.TestCase):
    """Tích hợp preference vào cơ chế scoring hiện tại."""

    def setUp(self) -> None:
        self.food_criteria = [
            {"domain": "food", "name": "Giá", "direction": "min", "weight": Decimal("0.4000")},
            {
                "domain": "food",
                "name": "Mức phù hợp nhu cầu/khẩu vị",
                "direction": "max",
                "weight": Decimal("0.3500"),
            },
            {
                "domain": "food",
                "name": "Thời gian chuẩn bị",
                "direction": "min",
                "weight": Decimal("0.2500"),
            },
        ]
        self.candidates = [
            {"id": 1, "name": "Món A", "price": 30_000, "prep_time": 15, "tags": ["high_protein", "low_oil"]},
            {
                "id": 2,
                "name": "Món B",
                "price": 30_000,
                "prep_time": 15,
                "tags": ["high_protein", "low_oil", "non_spicy"],
            },
            {"id": 3, "name": "Món C", "price": 30_000, "prep_time": 15, "tags": ["spicy", "high_fat"]},
        ]

    def test_preference_scored_by_tag_matching(self) -> None:
        scored = score_candidates(self.candidates, self.food_criteria, user_preferences=USER_PREFERENCES)

        # Món B khớp 3/3 → 100.0, Món A khớp 2/3 → 66.67, Món C khớp 0/3 → 0.0
        self.assertEqual(scored[1]["criteria_scores"]["preference"], 100.0)
        self.assertEqual(scored[0]["criteria_scores"]["preference"], 66.67)
        self.assertEqual(scored[2]["criteria_scores"]["preference"], 0.0)

    def test_candidate_without_tags_gets_zero_preference(self) -> None:
        candidates = [{"id": 1, "name": "Món A", "price": 30_000, "prep_time": 15}]
        scored = score_candidates(candidates, self.food_criteria, user_preferences=USER_PREFERENCES)
        self.assertEqual(scored[0]["criteria_scores"]["preference"], 0.0)

    def test_empty_user_preferences_gives_neutral_preference(self) -> None:
        """Không có sở thích → mọi ứng viên cùng điểm trung tính 50.0."""
        scored = score_candidates(self.candidates, self.food_criteria, user_preferences=[])
        for item in scored:
            self.assertEqual(item["criteria_scores"]["preference"], 50.0)

    def test_price_and_prep_time_unaffected_by_preference(self) -> None:
        """Chấm điểm preference không làm thay đổi điểm price/prep_time."""
        without = score_candidates(self.candidates, self.food_criteria)
        with_pref = score_candidates(self.candidates, self.food_criteria, user_preferences=USER_PREFERENCES)

        for a, b in zip(without, with_pref, strict=True):
            self.assertEqual(a["criteria_scores"]["price"], b["criteria_scores"]["price"])
            self.assertEqual(a["criteria_scores"]["prep_time"], b["criteria_scores"]["prep_time"])

    def test_legacy_caller_without_preferences_still_works(self) -> None:
        """Caller cũ (không truyền sở thích) giữ hành vi Min-Max như cũ."""
        candidates = [
            {"id": 1, "name": "Món A", "price": 30_000, "preference": 80, "prep_time": 15},
            {"id": 2, "name": "Món B", "price": 40_000, "preference": 40, "prep_time": 10},
        ]
        scored = score_candidates(candidates, self.food_criteria)
        self.assertEqual(scored[0]["criteria_scores"]["preference"], 100.0)
        self.assertEqual(scored[1]["criteria_scores"]["preference"], 0.0)


class TestPreferenceInPipeline(unittest.TestCase):
    """Tích hợp Engine: preference tham gia WSM và phản ánh vào thứ hạng."""

    def setUp(self) -> None:
        self.food_criteria = [
            {"domain": "food", "name": "Giá", "direction": "min", "weight": Decimal("0.4000")},
            {
                "domain": "food",
                "name": "Mức phù hợp nhu cầu/khẩu vị",
                "direction": "max",
                "weight": Decimal("0.3500"),
            },
            {
                "domain": "food",
                "name": "Thời gian chuẩn bị",
                "direction": "min",
                "weight": Decimal("0.2500"),
            },
        ]
        # Giá và thời gian chuẩn bị giống nhau → chỉ preference phân biệt thứ hạng.
        self.candidates = [
            {"id": 1, "name": "Món A", "price": 30_000, "prep_time": 15, "tags": ["high_protein", "low_oil"]},
            {
                "id": 2,
                "name": "Món B",
                "price": 30_000,
                "prep_time": 15,
                "tags": ["high_protein", "low_oil", "non_spicy"],
            },
            {"id": 3, "name": "Món C", "price": 30_000, "prep_time": 15, "tags": ["spicy", "high_fat"]},
        ]

    def test_ranking_reflects_preference_difference(self) -> None:
        results = evaluate(
            self.candidates,
            self.food_criteria,
            domain="food",
            user_preferences=USER_PREFERENCES,
        )
        self.assertEqual([r["name"] for r in results], ["Món B", "Món A", "Món C"])
        self.assertEqual([r["rank"] for r in results], [1, 2, 3])

    def test_preference_uses_existing_weight_in_wsm(self) -> None:
        """Điểm WSM = w_price×price + w_pref×preference + w_prep×prep_time."""
        results = evaluate(
            self.candidates,
            self.food_criteria,
            domain="food",
            user_preferences=USER_PREFERENCES,
        )
        by_name = {r["name"]: r for r in results}

        # price và prep_time đều bằng nhau trên cả 3 món → min=max → 100.0 mỗi món.
        # Món B: 0.4×100 + 0.35×100 + 0.25×100 = 100.00
        # Món A: 0.4×100 + 0.35×66.67 + 0.25×100 = 88.33
        # Món C: 0.4×100 + 0.35×0 + 0.25×100 = 65.00
        self.assertEqual(by_name["Món B"]["score"], 100.00)
        self.assertEqual(by_name["Món A"]["score"], 88.33)
        self.assertEqual(by_name["Món C"]["score"], 65.00)

    def test_wsm_score_stays_in_valid_range(self) -> None:
        results = evaluate(
            self.candidates,
            self.food_criteria,
            domain="food",
            user_preferences=USER_PREFERENCES,
        )
        for r in results:
            self.assertGreaterEqual(r["score"], 0.0)
            self.assertLessEqual(r["score"], 100.0)

    def test_pipeline_without_preferences_unchanged(self) -> None:
        """Pipeline không truyền sở thích → hành vi cũ, không lỗi."""
        candidates = [
            {"id": 1, "name": "Món X", "price": 50_000, "preference": 80, "prep_time": 20},
            {"id": 2, "name": "Món Y", "price": 30_000, "preference": 80, "prep_time": 20},
        ]
        results = evaluate(candidates, self.food_criteria, domain="food")
        self.assertEqual(results[0]["name"], "Món Y")


if __name__ == "__main__":
    unittest.main()
