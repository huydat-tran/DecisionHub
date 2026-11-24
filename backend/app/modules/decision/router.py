"""Router API cho module Decision."""

import logging

from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.common.exceptions import DecisionHubException
from app.core.database import get_db
from app.modules.auth.dependencies import bearer_scheme, get_current_user
from app.modules.decision.decision_response import DecisionResponse
from app.modules.decision.mock_data import build_mock_response
from app.modules.decision.schema import (
    DecisionHistoryDetailResponse,
    DecisionHistoryListResponse,
    DecisionRecommendRequest,
)
from app.modules.decision.service import (
    get_user_decision_detail,
    list_user_decision_history,
    recommend_food_decisions,
)
from app.modules.users.models import User

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Decisions"])


def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> User | None:
    """Xác thực người dùng từ Bearer token nếu client có gửi Authorization header.

    - Nếu có gửi header Authorization: kiểm tra JWT nghiêm ngặt qua `get_current_user`
      (trả 401 nếu token sai/hết hạn) và trả về đối tượng User để lưu lịch sử.
    - Nếu không gửi header Authorization: trả về None (cho phép Guest recommend).
    """
    if credentials is None:
        return None
    return get_current_user(credentials=credentials, db=db)


@router.post(
    "/api/v1/decisions/food/recommend",
    response_model=DecisionResponse,
    summary="Gợi ý món ăn theo tiêu chí WSM (Decision Engine)",
)
@router.post(
    "/api/v1/decisions/recommend",
    response_model=DecisionResponse,
    summary="Gợi ý theo tiêu chí WSM và thống kê phương án bị loại",
)
@router.post(
    "/decisions/food/recommend",
    response_model=DecisionResponse,
    summary="Gợi ý món ăn theo tiêu chí WSM và lưu lịch sử quyết định",
)
@router.post(
    "/decisions/recommend",
    response_model=DecisionResponse,
    summary="Gợi ý theo tiêu chí WSM và lưu lịch sử quyết định",
)
def recommend_decisions(
    payload: DecisionRecommendRequest,
    db: Session = Depends(get_db),  # noqa: B008
    current_user: User | None = Depends(get_optional_current_user),  # noqa: B008
) -> DecisionResponse:
    """Đánh giá và gợi ý theo WSM kết hợp thống kê phương án bị loại và lưu lịch sử."""
    user_id = current_user.id if isinstance(current_user, User) else None
    try:
        return recommend_food_decisions(db=db, payload=payload, user_id=user_id)
    except DecisionHubException as exc:
        if exc.status_code == 400 or user_id is not None:
            raise
        logger.warning(
            "Không thể truy vấn DB (%s), chạy Decision Engine với dữ liệu mẫu.",
            exc,
        )
        return build_mock_response(payload)
    except Exception as exc:
        if user_id is not None:
            raise
        logger.warning(
            "Không thể truy vấn DB (%s), chạy Decision Engine với dữ liệu mẫu.",
            exc,
        )
        return build_mock_response(payload)


@router.get(
    "/api/v1/decisions/history",
    response_model=DecisionHistoryListResponse,
    summary="Xem danh sách lịch sử quyết định của người dùng hiện tại",
)
@router.get(
    "/decisions/history",
    response_model=DecisionHistoryListResponse,
    summary="Xem danh sách lịch sử quyết định của người dùng hiện tại",
)
def get_decision_history_list(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Số lượng bản ghi tối đa trên mỗi trang (1-100)",
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Vị trí bắt đầu phân trang",
    ),
    db: Session = Depends(get_db),  # noqa: B008
    current_user: User = Depends(get_current_user),  # noqa: B008
) -> DecisionHistoryListResponse:
    """Lấy danh sách lịch sử quyết định của chính người dùng đang đăng nhập (mới nhất trước)."""
    return list_user_decision_history(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/api/v1/decisions/history/{decision_id}",
    response_model=DecisionHistoryDetailResponse,
    summary="Xem chi tiết một quyết định đã lưu",
)
@router.get(
    "/decisions/history/{decision_id}",
    response_model=DecisionHistoryDetailResponse,
    summary="Xem chi tiết một quyết định đã lưu",
)
def get_decision_history_detail(
    decision_id: int,
    db: Session = Depends(get_db),  # noqa: B008
    current_user: User = Depends(get_current_user),  # noqa: B008
) -> DecisionHistoryDetailResponse:
    """Lấy chi tiết một bản ghi lịch sử quyết định thuộc về người dùng đang đăng nhập."""
    return get_user_decision_detail(
        db=db,
        decision_id=decision_id,
        user_id=current_user.id,
    )

