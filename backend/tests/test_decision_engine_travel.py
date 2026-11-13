from app.modules.decision.engine.calculator import (
    Criterion,
    build_explanations,
    score_candidates,
)
from app.modules.decision.engine.ranking import rank_candidates


def test_score_and_rank_candidates():
    criteria = [
        Criterion(key="cost", name="Chi phí du lịch", direction="min", weight=0.40),
        Criterion(key="preference", name="Mức phù hợp sở thích", direction="max", weight=0.35),
        Criterion(key="duration", name="Thời lượng trải nghiệm", direction="min", weight=0.25),
    ]

    candidates = [
        {
            "place_id": 1,
            "name": "Địa điểm A",
            "cost": 500000.0,
            "duration": 8.0,
            "preference": 80.0,
        },
        {
            "place_id": 2,
            "name": "Địa điểm B",
            "cost": 1000000.0,
            "duration": 12.0,
            "preference": 90.0,
        },
        {
            "place_id": 3,
            "name": "Địa điểm C",
            "cost": 300000.0,
            "duration": 4.0,
            "preference": 70.0,
        },
    ]

    scored = score_candidates(candidates, criteria)
    assert len(scored) == 3
    for c in scored:
        assert "score" in c
        assert "criteria_scores" in c
        assert 0 <= c["score"] <= 100

    ranked = rank_candidates(scored, top_n=2, cost_key="cost", name_key="name")
    assert len(ranked) == 2
    # Địa điểm đầu tiên phải có score cao nhất hoặc chi phí thấp hơn nếu bằng điểm
    assert ranked[0]["score"] >= ranked[1]["score"]

    # Test explanation
    filters = {"budget_max": 1000000, "max_duration": 15.0}
    reasons = build_explanations(ranked[0], criteria, filters)
    assert len(reasons) > 0
    assert any("Chi phí" in r for r in reasons)
