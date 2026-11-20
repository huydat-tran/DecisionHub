"""Pipeline quyết định dùng chung: lọc tiêu chí theo domain, lọc ứng viên, chấm điểm, xếp hạng.

Luồng: filters.py → scoring.py → calculator.py → ranking.py
"""

from collections.abc import Sequence
from typing import Any

from app.modules.decision.engine.calculator import calculate_wsm
from app.modules.decision.engine.filters import (
    Constraints,
    filter_and_explain_candidates,
)
from app.modules.decision.engine.ranking import rank_candidates
from app.modules.decision.engine.scoring import score_candidates
from app.modules.decision.models import DECISION_DOMAINS

# Số phương án bị loai tối đa được trả về chi tiết trong response.
# total_excluded luôn là tổng số bị loại (không bị cắt), còn danh sách chi tiết
# chỉ giữ tối đa số lượng này để response không phình to vô hạn.
MAX_EXCLUDED_DETAIL: int = 20


def select_criteria(criteria: list, domain: str) -> list:
    """Giữ lại tiêu chí thuộc đúng domain được yêu cầu."""
    if domain not in DECISION_DOMAINS:
        raise ValueError(f"Domain không hợp lệ: {domain}")
    return [
        criterion
        for criterion in criteria
        if (
            criterion.get("domain")
            if isinstance(criterion, dict)
            else getattr(criterion, "domain", None)
        )
        == domain
    ]


def evaluate_decision(
    candidates: Sequence[Any],
    criteria: list,
    domain: str,
    constraints: Constraints | None = None,
    user_preferences: Sequence[str] | None = None,
    limit: int | None = None,
    **legacy: Any,
) -> dict[str, Any]:
    """Chạy toàn bộ quy trình Decision Engine với thống kê phương án bị loại.

    Luồng:
      1. select_criteria()           → lọc tiêu chí theo domain.
      2. Kiểm tra candidates đầu vào → nếu rỗng, dừng ngay.
      3. filter_and_explain_candidates() → phân tách phương án hợp lệ và bị loại.
      4. Kiểm tra valid_candidates   → nếu không còn phương án hợp lệ nào,
         TUYỆT ĐỐI KHÔNG CHẠY Scoring hay WSM, trả về thông báo và danh sách bị loại.
      5. score_candidates()          → chỉ chuẩn hóa điểm trên các phương án hợp lệ.
      6. calculate_wsm()             → tính tổng điểm WSM và contribution từng tiêu chí.
      7. rank_candidates()           → sắp xếp giảm dần và gán thứ hạng rank.

    Args:
        candidates: Danh sách phương án ban đầu.
        criteria: Danh sách tiêu chí (DecisionCriterion).
        domain: Domain đánh giá ("food" hoặc "travel").
        constraints: Cấu hình điều kiện bắt buộc {field_name: (operator, giá trị)}.
        user_preferences: Sở thích/tag của người dùng.
        limit: Số lượng phương án tối đa lấy ra sau khi xếp hạng.
        **legacy: Tham số cũ (budget_max, meal_type, max_prep_time, excluded_ingredients).

    Returns:
        dict chứa:
        - success: bool
        - has_valid_candidates: bool (True nếu còn ít nhất 1 phương án hợp lệ)
        - message: str (thông báo kết quả đánh giá)
        - valid_candidates: list[dict] (các phương án hợp lệ có đủ total_score, rank, criteria_details)
        - excluded_candidates: list[dict] (các phương án bị loại có id, name, status, exclusion_reason;
            tối đa MAX_EXCLUDED_DETAIL mục)
        - total_valid: int (tổng số phương án hợp lệ TRƯỚC khi áp dụng limit)
        - returned_count: int (số phương án thực tế được trả về sau khi áp dụng limit)
        - total_excluded: int (TỔNG số phương án bị loại, không bị cắt)
        - excluded_returned_count: int (số mục chi tiết bị loại thực sự được trả về)
    """
    selected = select_criteria(criteria, domain)

    # 1. Kiểm tra danh sách ứng viên ban đầu
    if not candidates:
        return {
            "success": True,
            "has_valid_candidates": False,
            "message": "Không có phương án nào được cung cấp để đánh giá.",
            "valid_candidates": [],
            "excluded_candidates": [],
            "total_valid": 0,
            "returned_count": 0,
            "total_excluded": 0,
            "excluded_returned_count": 0,
        }

    # 2. Phân tách ứng viên hợp lệ và ứng viên bị loại theo Hard Constraints
    valid_candidates, excluded_candidates = filter_and_explain_candidates(
        candidates, constraints, domain=domain, **legacy
    )

    # total_excluded = tổng số phương án bị loại (KHÔNG bị cắt).
    # excluded_candidates chỉ trả về tối đa MAX_EXCLUDED_DETAIL mục chi tiết
    # để response không phình to theo số lượng ứng viên bị loại.
    total_excluded = len(excluded_candidates)
    excluded_detail = excluded_candidates[:MAX_EXCLUDED_DETAIL]

    # 3. YÊU CẦU QUAN TRỌNG: Không chạy Scoring khi không còn ứng viên hợp lệ
    if not valid_candidates:
        return {
            "success": True,
            "has_valid_candidates": False,
            "message": (
                "Không có phương án hợp lệ để đánh giá do tất cả phương án "
                "đều đã bị loại bởi điều kiện bắt buộc."
            ),
            "valid_candidates": [],
            "excluded_candidates": excluded_detail,
            "total_valid": 0,
            "returned_count": 0,
            "total_excluded": total_excluded,
            "excluded_returned_count": len(excluded_detail),
        }

    # 4. Chỉ thực hiện Scoring và WSM trên các ứng viên hợp lệ
    scored = score_candidates(
        valid_candidates, selected, user_preferences=user_preferences
    )
    calculated = calculate_wsm(scored, selected)
    ranked = rank_candidates(calculated, limit=limit)

    # total_valid = tổng số ứng viên hợp lệ TRƯỚC khi áp dụng limit.
    # returned_count = số ứng viên thực tế được trả về sau limit.
    total_valid = len(valid_candidates)
    returned_count = len(ranked)
    if limit is not None and limit > 0 and returned_count < total_valid:
        message = (
            f"Đánh giá thành công {total_valid} phương án hợp lệ, "
            f"trả về {returned_count} phương án theo giới hạn."
        )
    else:
        message = f"Đánh giá thành công {total_valid} phương án hợp lệ."

    return {
        "success": True,
        "has_valid_candidates": True,
        "message": message,
        "valid_candidates": ranked,
        "excluded_candidates": excluded_detail,
        "total_valid": total_valid,
        "returned_count": returned_count,
        "total_excluded": total_excluded,
        "excluded_returned_count": len(excluded_detail),
    }


def evaluate(
    candidates: Sequence[Any],
    criteria: list,
    domain: str,
    constraints: Constraints | None = None,
    user_preferences: Sequence[str] | None = None,
    **legacy: Any,
) -> list[dict]:
    """Chạy pipeline WSM cho một domain (tương thích ngược với các hàm gọi cũ).

    Trả về trực tiếp danh sách valid_candidates đã được xếp hạng.
    """
    result = evaluate_decision(
        candidates=candidates,
        criteria=criteria,
        domain=domain,
        constraints=constraints,
        user_preferences=user_preferences,
        **legacy,
    )
    return result["valid_candidates"]
