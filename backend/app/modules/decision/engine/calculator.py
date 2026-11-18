"""Decision Engine - Module tính điểm WSM (Weighted Sum Model).

Hai tầng trách nhiệm:
1. Pipeline chung (calculate_wsm, validate_weights):
   - Nhận ứng viên đã có criteria_scores từ scoring.py.
   - Kiểm tra weight hợp lệ, tính tổng Σ(weight × normalized_score).
   - Gắn kết quả vào trường `score` của từng ứng viên.
2. Food-specific (calculate_food_wsm và các hàm con):
   - Tính điểm từng tiêu chí theo API Contract Food Recommend.
   - Giữ nguyên để tương thích với code hiện tại của module food.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
import math
from typing import Any

from app.modules.decision.engine.scoring import CRITERION_FIELD_MAP

# ---------------------------------------------------------------------------
# Trọng số FALLBACK (chỉ dùng khi repository không lấy được dữ liệu từ DB)
# ---------------------------------------------------------------------------
WEIGHT_PRICE: float = 0.40
WEIGHT_PREFERENCE: float = 0.35
WEIGHT_PREP_TIME: float = 0.25

# Điểm trung tính cho các tiêu chí không được người dùng yêu cầu lọc
NEUTRAL_SCORE: float = 50.0


@dataclass(frozen=True)
class CriteriaScoresResult:
    """Điểm chuẩn hóa của từng tiêu chí (thang điểm 0.0 - 100.0)."""

    price: float
    preference: float
    prep_time: float

    def to_dict(self, rounded: bool = False) -> dict[str, float]:
        """Chuyển thành dictionary (tùy chọn làm tròn 2 chữ số cho response)."""
        if rounded:
            return {
                "price": round(self.price, 2),
                "preference": round(self.preference, 2),
                "prep_time": round(self.prep_time, 2),
            }
        return {
            "price": self.price,
            "preference": self.preference,
            "prep_time": self.prep_time,
        }


@dataclass(frozen=True)
class FoodWSMResult:
    """Kết quả tính điểm WSM tổng hợp của một món ăn."""

    score: float  # Điểm số thực chưa làm tròn (dùng để xếp hạng chính xác)
    criteria_scores: CriteriaScoresResult

    @property
    def rounded_score(self) -> float:
        """Tổng điểm làm tròn 2 chữ số thập phân khi serialize response hiển thị."""
        return round(self.score, 2)


# ==============================================================================
# CÁC HÀM TÍNH ĐIỂM TIÊU CHÍ CON (CRITERIA SCORING)
# ==============================================================================


def calculate_price_score(price: float, budget_max: float) -> float:
    """Tiêu chí 1: Giá (Hướng COST ↓ - giá càng rẻ so với ngân sách thì điểm càng cao).

    Công thức API Contract:
        price_score = 100 * (1 - price / budget_max)
    Ví dụ: Ngân sách 50k, món 30k -> 100 * (1 - 30/50) = 40.0 điểm.
    """
    if budget_max <= 0 or price > budget_max:
        return 0.0

    raw_score = 100.0 * (1.0 - (price / budget_max))
    return max(0.0, min(100.0, raw_score))


def calculate_preference_score(
    food_tags: Sequence[str] | set[str] | None,
    preferred_tags: Sequence[str] | set[str] | None,
) -> float:
    """Tiêu chí 2: Sở thích (Hướng BENEFIT ↑ - khớp càng nhiều tag người dùng chọn thì điểm càng cao).

    Công thức API Contract:
    - Nếu có chọn tag: 100 * (số tag khớp / tổng tag người dùng chọn)
    - Nếu KHÔNG chọn tag: mặc định 50.0 (điểm trung tính).
    Ví dụ: Người dùng chọn 2 tags, món khớp 1 tag -> 100 * (1/2) = 50.0 điểm.
    """
    if not preferred_tags:
        return NEUTRAL_SCORE

    # Chuẩn hóa chữ thường và bỏ khoảng trắng thừa
    user_tags = {t.strip().lower() for t in preferred_tags if t and t.strip()}
    if not user_tags:
        return NEUTRAL_SCORE

    dish_tags = {t.strip().lower() for t in food_tags if t and t.strip()} if food_tags else set()

    matched_count = len(user_tags.intersection(dish_tags))
    raw_score = 100.0 * (matched_count / len(user_tags))
    return max(0.0, min(100.0, raw_score))


def calculate_prep_time_score(prep_time: float, max_prep_time: float | None) -> float:
    """Tiêu chí 3: Thời gian chuẩn bị (Hướng COST ↓ - thời gian càng ngắn thì điểm càng cao).

    Công thức API Contract:
    - Nếu có đặt max_prep_time: 100 * (1 - prep_time / max_prep_time)
    - Nếu KHÔNG đặt max_prep_time: mặc định 50.0 (điểm trung tính).
    Ví dụ: Giới hạn 30 phút, món làm mất 15 phút -> 100 * (1 - 15/30) = 50.0 điểm.
    """
    if max_prep_time is None or max_prep_time <= 0:
        return NEUTRAL_SCORE

    if prep_time > max_prep_time:
        return 0.0

    raw_score = 100.0 * (1.0 - (prep_time / max_prep_time))
    return max(0.0, min(100.0, raw_score))


# ==============================================================================
# HÀM TỔNG HỢP ĐIỂM WSM CHÍNH
# ==============================================================================


def calculate_food_wsm(
    price: float,
    prep_time: float,
    food_tags: Sequence[str] | set[str] | None,
    budget_max: float,
    max_prep_time: float | None = None,
    preferred_tags: Sequence[str] | set[str] | None = None,
    weights: dict[str, float] | None = None,
) -> FoodWSMResult:
    """Hàm tính điểm WSM chính cho một món ăn theo đúng API Contract.

    Công thức:
        Total Score = (w_price * price_score) + (w_pref * pref_score) + (w_prep * prep_score)

    Args:
        price: Giá món ăn (VND).
        prep_time: Thời gian chuẩn bị (phút).
        food_tags: Danh sách tag của món ăn.
        budget_max: Ngân sách tối đa người dùng nhập.
        max_prep_time: Giới hạn thời gian chuẩn bị (None = không giới hạn).
        preferred_tags: Tag ưa thích người dùng chọn (None = không chọn).
        weights: Trọng số từ DB (load bằng load_food_weights).
                 Nếu None → tự dùng hằng số FALLBACK.

    Returns:
        FoodWSMResult: Chứa tổng điểm `score` (số thực chưa làm tròn) và chi tiết `criteria_scores`.
    """
    # Dùng trọng số từ DB nếu có, ngược lại dùng hằng số fallback
    w_price = weights["price"] if weights else WEIGHT_PRICE
    w_pref = weights["preference"] if weights else WEIGHT_PREFERENCE
    w_prep = weights["prep_time"] if weights else WEIGHT_PREP_TIME

    # 1. Tính điểm chuẩn hóa từng tiêu chí (0.0 - 100.0)
    price_score = calculate_price_score(price, budget_max)
    pref_score = calculate_preference_score(food_tags, preferred_tags)
    prep_score = calculate_prep_time_score(prep_time, max_prep_time)

    # 2. Nhân trọng số và cộng dồn WSM
    total_score = (
        (w_price * price_score)
        + (w_pref * pref_score)
        + (w_prep * prep_score)
    )

    # 3. Giới hạn trong khoảng [0.0, 100.0]
    final_score = max(0.0, min(100.0, total_score))

    return FoodWSMResult(
        score=final_score,
        criteria_scores=CriteriaScoresResult(
            price=price_score,
            preference=pref_score,
            prep_time=prep_score,
        ),
    )


# Alias tương thích
calculate_wsm_score = calculate_food_wsm


# ==============================================================================
# PIPELINE CHUNG: validate_weights() và calculate_wsm()
# ==============================================================================

# Dung sai cho phép khi kiểm tra tổng weight == 1.0
_WEIGHT_SUM_TOLERANCE: float = 1e-9


def _to_numeric_weight(raw: Any) -> float | None:
    """Chuyển giá trị weight thô sang float hợp lệ; trả None nếu không hợp lệ."""
    if raw is None or isinstance(raw, bool):
        return None
    if isinstance(raw, (int, float, Decimal)):
        val = float(raw)
        return val if math.isfinite(val) else None
    try:
        val = float(str(raw).strip())
    except (TypeError, ValueError):
        return None
    return val if math.isfinite(val) else None


def validate_weights(
    criteria: list[Any] | dict[str, Any],
) -> dict[str, float]:
    """Kiểm tra danh sách hoặc dict trọng số; trả về dict {field_name: weight}.

    Quy tắc:
    - Mỗi weight phải là số hữu hạn, không âm.
    - Tổng các weight phải bằng 1.0 (sai số cho phép 1e-9).
    - Danh sách rỗng hoặc dict rỗng đều bị từ chối.

    Args:
        criteria: Danh sách dict tiêu chí có key 'name'/'field_name' và 'weight',
                  hoặc dict trực tiếp {field_name: weight}.

    Returns:
        Dict {field_name: weight (float)}.

    Raises:
        ValueError: Khi weight không hợp lệ hoặc tổng khác 1.0.
    """
    if not criteria:
        raise ValueError("Danh sách tiêu chí không được rỗng.")

    result: dict[str, float] = {}

    if isinstance(criteria, dict):
        for field, raw in criteria.items():
            w = _to_numeric_weight(raw)
            if w is None:
                raise ValueError(f"Weight không hợp lệ cho trường {field!r}: {raw!r}")
            if w < 0:
                raise ValueError(f"Weight không được âm cho trường {field!r}: {w}")
            result[str(field)] = w
    else:
        for item in criteria:
            # Lấy tên trường
            name = str((item.get("name") if isinstance(item, dict) else getattr(item, "name", "")) or "").strip()
            explicit_field = (item.get("field_name") if isinstance(item, dict) else getattr(item, "field_name", None))
            if explicit_field:
                field_name = str(explicit_field).strip()
            else:
                field_name = CRITERION_FIELD_MAP.get(name.lower(), name)

            raw = item.get("weight") if isinstance(item, dict) else getattr(item, "weight", None)
            w = _to_numeric_weight(raw)
            if w is None:
                raise ValueError(f"Weight không hợp lệ cho tiêu chí {name!r}: {raw!r}")
            if w < 0:
                raise ValueError(f"Weight không được âm cho tiêu chí {name!r}: {w}")
            result[field_name] = w

    total = sum(result.values())
    if abs(total - 1.0) > _WEIGHT_SUM_TOLERANCE:
        raise ValueError(
            f"Tổng weight phải bằng 1.0, hiện tại là {total:.10f}. "
            "Hãy kiểm tra lại các trọng số trong bảng decision_criteria."
        )

    return result


def calculate_wsm(
    candidates: list[dict[str, Any]],
    criteria: list[Any] | dict[str, Any],
) -> list[dict[str, Any]]:
    """Tính tổng điểm WSM cho danh sách ứng viên đã có criteria_scores.

    Công thức: total_score = Σ(weight × normalized_score)
    - Tiêu chí có normalized_score là None không đóng góp vào tổng.
    - Kết quả được làm tròn 2 chữ số thập phân và giới hạn trong [0.0, 100.0].
    - Không mutate dict ứng viên đầu vào.

    Args:
        candidates: Danh sách ứng viên đã qua score_candidates() (có trường criteria_scores).
        criteria: Tiêu chí kèm weight (list hoặc dict).

    Returns:
        Danh sách dict mới, mỗi dict có thêm trường `score`.
    """
    if not candidates:
        return []

    weights = validate_weights(criteria)

    results: list[dict[str, Any]] = []
    for cand in candidates:
        out = dict(cand)
        criteria_scores: dict[str, Any] = out.get("criteria_scores", {})

        total = 0.0
        for field_name, w in weights.items():
            s = criteria_scores.get(field_name)
            if s is not None:
                total += w * float(s)

        # Giới hạn [0.0, 100.0] và làm tròn 2 chữ số
        out["score"] = round(max(0.0, min(100.0, total)), 2)
        results.append(out)

    return results
