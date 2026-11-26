"""Router API cho module Travel."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.travel.schemas import (
    TravelRecommendRequest,
    TravelRecommendResponse,
)
from app.modules.decision.service import recommend_travel

router = APIRouter(prefix="/api/v1/travel", tags=["Travel"])


@router.post(
    "/recommend",
    response_model=TravelRecommendResponse,
    summary="Gợi ý địa điểm du lịch theo tiêu chí (WSM)",
)
def recommend(
    payload: TravelRecommendRequest,
    db: Session = Depends(get_db),  # noqa: B008
) -> TravelRecommendResponse:
    """Nhận tiêu chí từ client, lọc điều kiện ngân sách/thời lượng, chấm điểm WSM và xếp hạng Top N."""
    data, message = recommend_travel(db=db, payload=payload)
    return TravelRecommendResponse(success=True, message=message, data=data)
