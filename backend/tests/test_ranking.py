"""Unit tests cho Bước 5 - Ranking (sắp xếp giảm dần, tie-break ổn định)."""

from pathlib import Path
import sys
import unittest

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.modules.decision.engine.ranking import rank_candidates


class TestRanking(unittest.TestCase):

    def test_empty_candidates_returns_empty(self) -> None:
        """Danh sách rỗng → trả danh sách rỗng."""
        self.assertEqual(rank_candidates([]), [])

    def test_rank_candidates_descending_score(self) -> None:
        """Sắp xếp theo điểm giảm dần, gắn rank đúng."""
        candidates = [
            {"id": 1, "name": "Món B", "price": 40000, "score": 42.17},
            {"id": 2, "name": "Món A", "price": 30000, "score": 63.50},
            {"id": 3, "name": "Món C", "price": 20000, "score": 49.83},
        ]
        ranked = rank_candidates(candidates)

        # Thứ tự đúng: Món A (63.50) → Món C (49.83) → Món B (42.17)
        self.assertEqual([r["name"] for r in ranked], ["Món A", "Món C", "Món B"])
        self.assertEqual([r["rank"] for r in ranked], [1, 2, 3])

    def test_tie_break_level_1_lower_cost_priority(self) -> None:
        """Hai ứng viên bằng điểm → ưu tiên ứng viên có chi phí thấp hơn."""
        candidates = [
            {"id": 1, "name": "Phở Gà", "price": 60000, "score": 50.00},
            {"id": 2, "name": "Bún Riêu", "price": 50000, "score": 50.00},
        ]
        ranked = rank_candidates(candidates)

        # Bún Riêu (50k) rẻ hơn Phở Gà (60k) → Bún Riêu rank 1
        self.assertEqual(ranked[0]["name"], "Bún Riêu")
        self.assertEqual(ranked[0]["rank"], 1)
        self.assertEqual(ranked[1]["name"], "Phở Gà")
        self.assertEqual(ranked[1]["rank"], 2)

    def test_tie_break_level_2_same_score_same_cost_sort_by_name(self) -> None:
        """Bằng điểm và bằng chi phí → sắp xếp theo tên A-Z."""
        candidates = [
            {"id": 2, "name": "Canh Bún", "price": 50000, "score": 50.00},
            {"id": 1, "name": "Bún Riêu", "price": 50000, "score": 50.00},
        ]
        ranked = rank_candidates(candidates)

        # "bún riêu" (B) trước "canh bún" (C)
        self.assertEqual(ranked[0]["name"], "Bún Riêu")
        self.assertEqual(ranked[1]["name"], "Canh Bún")

    def test_tie_break_level_3_same_score_cost_name_sort_by_id(self) -> None:
        """Bằng điểm, bằng chi phí, bằng cả tên → theo ID tăng dần."""
        candidates = [
            {"id": 108, "name": "Bún Bò", "price": 45000, "score": 60.00},
            {"id": 105, "name": "Bún Bò", "price": 45000, "score": 60.00},
        ]
        ranked = rank_candidates(candidates)

        # ID 105 < 108 → ID 105 đứng trước
        self.assertEqual(ranked[0]["id"], 105)
        self.assertEqual(ranked[1]["id"], 108)

    def test_tie_break_identical_candidates_preserves_original_order(self) -> None:
        """Hai ứng viên hoàn toàn bằng nhau mọi tiêu chí → giữ nguyên thứ tự ban đầu (stable)."""
        candidates = [
            {"id": 1, "name": "Bánh Mì", "price": 20000, "score": 50.00, "note": "item_dau"},
            {"id": 1, "name": "Bánh Mì", "price": 20000, "score": 50.00, "note": "item_sau"},
        ]
        ranked = rank_candidates(candidates)

        self.assertEqual(ranked[0]["note"], "item_dau")
        self.assertEqual(ranked[1]["note"], "item_sau")

    def test_limit_top_n(self) -> None:
        """limit=N trả đúng N ứng viên điểm cao nhất."""
        candidates = [
            {"id": 1, "name": "A", "score": 90.0, "price": 10},
            {"id": 2, "name": "B", "score": 80.0, "price": 10},
            {"id": 3, "name": "C", "score": 70.0, "price": 10},
            {"id": 4, "name": "D", "score": 60.0, "price": 10},
        ]
        ranked = rank_candidates(candidates, limit=2)
        self.assertEqual(len(ranked), 2)
        self.assertEqual([r["name"] for r in ranked], ["A", "B"])

    def test_does_not_mutate_input(self) -> None:
        """rank_candidates() không được sửa dict ứng viên gốc."""
        original = {"id": 1, "name": "X", "price": 10, "score": 80.0}
        rank_candidates([original])
        self.assertNotIn("rank", original)


if __name__ == "__main__":
    unittest.main()
