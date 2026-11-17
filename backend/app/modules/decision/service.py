"""Service cho module Decision — điều phối nghiệp vụ giữa repository và engine.

Nhận request từ router, gọi repository để lấy dữ liệu,
sau đó gọi Decision Engine để tính điểm và trả kết quả.
Không chứa logic truy vấn DB và không chứa logic tính điểm trực tiếp.
"""

from sqlalchemy.orm import Session

from app.modules.decision.repository import get_weights_by_domain
from app.modules.decision.schema import DecisionRecommendRequest


def get_food_weights(db: Session) -> dict[str, float]:
    """Lấy trọng số WSM cho domain food từ DB.

    Service biết khi nào cần gọi repository và với tham số nào.
    Router không cần biết domain là gì, chỉ gọi service.

    Args:
        db: SQLAlchemy Session (inject từ Depends(get_db) ở router).

    Returns:
        dict[str, float]: Trọng số {"price": ..., "preference": ..., "prep_time": ...}.
    """
    return get_weights_by_domain(db, domain="food")


def get_travel_weights(db: Session) -> dict[str, float]:
    """Lấy trọng số WSM cho domain travel từ DB.

    Bổ sung khi triển khai Travel (P1).

    Args:
        db: SQLAlchemy Session.

    Returns:
        dict[str, float]: Trọng số của các tiêu chí travel.
    """
    return get_weights_by_domain(db, domain="travel")
