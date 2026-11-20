"""Router API cho module Decision."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.exceptions import DecisionHubException
from app.core.database import get_db
from app.modules.decision.decision_response import DecisionResponse
from app.modules.decision.mock_data import build_mock_response
from app.modules.decision.schema import DecisionRecommendRequest
from app.modules.decision.service import recommend_food_decisions

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/decisions", tags=["Decisions"])


@router.post(
    "/food/recommend",
    response_model=DecisionResponse,
    summary="Gợi ý món ăn theo tiêu chí WSM (Decision Engine)",
)
@router.post(
    "/recommend",
    response_model=DecisionResponse,
    summary="Gợi ý theo tiêu chí WSM và thống kê phương án bị loại",
)
def recommend_decisions(
    payload: DecisionRecommendRequest,
    db: Session = Depends(get_db),  # noqa: B008
) -> DecisionResponse:
    """Đánh giá và gợi ý theo WSM kết hợp thống kê phương án bị loại."""
    try:
        return recommend_food_decisions(db=db, payload=payload)
    except DecisionHubException as exc:
        if exc.status_code == 400:
            raise
        logger.warning(
            "Không thể truy vấn DB (%s), chạy Decision Engine với dữ liệu mẫu.",
            exc,
        )
        return build_mock_response(payload)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Không thể truy vấn DB (%s), chạy Decision Engine với dữ liệu mẫu.",
            exc,
        )
        return build_mock_response(payload)
