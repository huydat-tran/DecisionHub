"""Router API cho module Decision."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.decision.decision_response import DecisionResponse
from app.modules.decision.schema import DecisionRecommendRequest
from app.modules.decision.service import recommend_food

router = APIRouter(prefix="/api/v1/decisions", tags=["Decisions"])


@router.post(
    "/food/recommend",
    response_model=DecisionResponse,
    summary="Gợi ý món ăn theo tiêu chí WSM (Decision Engine)",
)
@router.post(
    "/recommend",
    response_model=DecisionResponse,
    summary="Gợi ý món ăn theo tiêu chí WSM",
)
def recommend_decisions(
    payload: DecisionRecommendRequest,
    db: Session = Depends(get_db),  # noqa: B008
) -> DecisionResponse:
    """Gọi Decision Engine thông qua Service để lọc điều kiện bắt buộc, chấm điểm và xếp hạng."""
    return recommend_food(db=db, payload=payload)