"""Router API cho module Decision."""

from fastapi import APIRouter

from app.modules.decision.decision_request import DecisionRecommendRequest
from app.modules.decision.decision_response import DecisionResponse
from app.modules.decision.mock_data import build_mock_response

router = APIRouter(prefix="/api/v1/decisions", tags=["Decisions"])


@router.post(
    "/recommend",
    response_model=DecisionResponse,
    summary="Gợi ý theo tiêu chí WSM (dữ liệu giả)",
)
def recommend_decisions(payload: DecisionRecommendRequest) -> DecisionResponse:
    """TODO: thay build_mock_response bằng Decision Engine thật."""
    return build_mock_response(payload)