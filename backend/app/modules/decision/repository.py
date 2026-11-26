"""Repository cho module Decision — chịu trách nhiệm truy vấn database.

Chỉ chứa logic đọc dữ liệu từ DB, không có business logic.
Service gọi repository để lấy dữ liệu thô rồi chuyển đổi sang định dạng
đầu vào của Decision Engine.
"""

import logging
from decimal import Decimal
from typing import Any

import sqlalchemy as sa
from sqlalchemy import func, select
from sqlalchemy.orm import Session, raiseload, selectinload
from sqlalchemy.sql.elements import ColumnElement

from app.modules.decision.engine.filters import _as_list, _normalize_text, _to_number
from app.modules.decision.engine.pipeline import MAX_EXCLUDED_DETAIL
from app.modules.decision.models import Decision, DecisionCriterion, HardConstraint
from app.modules.food.models_food import Food, Ingredient

logger = logging.getLogger(__name__)

# Trọng số FALLBACK — dùng khi DB không có dữ liệu cho domain tương ứng.
# Key dùng field_name chuẩn (giống key Service trả về sau khi chuyển đổi).
_FALLBACK_WEIGHTS: dict[str, dict[str, float]] = {
    "food": {
        "price": 0.40,
        "preference": 0.35,
        "prep_time": 0.25,
    },
    "travel": {
        "estimated_cost": 0.40,
        "estimated_duration": 0.30,
        "activities": 0.30,
    },
}


def get_weights_by_domain(db: Session, domain: str) -> dict[str, float]:
    """Truy vấn trọng số WSM theo domain từ bảng `decision_criteria`.

    Query tất cả hàng có domain khớp, build dict: tên tiêu chí → trọng số.

    Key trả về là tên tiêu chí lưu trong DB (vd. "Giá"); Service chịu trách
    nhiệm ánh xạ sang `field_name` chuẩn (vd. "price") trước khi đưa vào
    Decision Engine.

    Ví dụ trả về cho domain='food':
        {"Giá": 0.40, "Mức phù hợp nhu cầu/khẩu vị": 0.35, "Thời gian chuẩn bị": 0.25}

    Nếu DB không có dữ liệu → dùng _FALLBACK_WEIGHTS[domain] và ghi log cảnh báo.

    Args:
        db: SQLAlchemy Session.
        domain: Tên domain cần lấy trọng số ("food" hoặc "travel").

    Returns:
        dict[str, float]: Mapping tên tiêu chí → trọng số (float).
    """
    rows: list[DecisionCriterion] = (
        db.query(DecisionCriterion)
        .filter(DecisionCriterion.domain == domain)
        .all()
    )

    if not rows:
        logger.warning(
            "Không tìm thấy dữ liệu trong decision_criteria (domain='%s'). "
            "Đang dùng trọng số FALLBACK mặc định.",
            domain,
        )
        return dict(_FALLBACK_WEIGHTS.get(domain, {}))

    # Build dict từ kết quả DB (Decimal → float)
    return {row.name: float(row.weight) for row in rows}


def get_hard_constraints_by_domain(db: Session, domain: str) -> list[dict[str, str]]:
    """Truy vấn cấu hình điều kiện bắt buộc theo domain từ bảng `hard_constraints`.

    Chỉ trả về các bản ghi `is_active = True`. Repository không kiểm tra
    `field_name`/`operator` có hợp lệ hay không — việc đó thuộc Service.

    Args:
        db: SQLAlchemy Session.
        domain: Tên domain cần lấy cấu hình ("food" hoặc "travel").

    Returns:
        list[dict[str, str]]: Danh sách {"name", "field_name", "operator"}.
    """
    rows: list[HardConstraint] = (
        db.query(HardConstraint)
        .filter(HardConstraint.domain == domain, HardConstraint.is_active.is_(True))
        .order_by(HardConstraint.id)
        .all()
    )

    if not rows:
        logger.warning(
            "Không tìm thấy hard_constraints đang active (domain='%s'). "
            "Ứng viên sẽ không bị áp dụng điều kiện lọc nào.",
            domain,
        )

    return [
        {"name": row.name, "field_name": row.field_name, "operator": row.operator}
        for row in rows
    ]


def get_criteria_by_domain(db: Session, domain: str) -> list[DecisionCriterion]:
    """Truy vấn danh sách tiêu chí đánh giá theo domain từ bảng `decision_criteria`.

    Trả về danh sách đối tượng DecisionCriterion đầy đủ (domain, name, direction, weight).
    Nếu DB không có dữ liệu cho domain tương ứng, trả về tiêu chí FALLBACK mặc định.

    Args:
        db: SQLAlchemy Session.
        domain: Tên domain cần lấy tiêu chí ("food" hoặc "travel").

    Returns:
        list[DecisionCriterion]: Danh sách bản ghi tiêu chí.
    """
    rows: list[DecisionCriterion] = (
        db.query(DecisionCriterion)
        .filter(DecisionCriterion.domain == domain)
        .all()
    )

    if not rows:
        logger.warning(
            "Không tìm thấy dữ liệu trong decision_criteria (domain='%s'). "
            "Đang dùng tiêu chí FALLBACK mặc định.",
            domain,
        )
        if domain == "food":
            return [
                DecisionCriterion(
                    domain="food",
                    name="Giá",
                    direction="min",
                    weight=Decimal("0.4000"),
                ),
                DecisionCriterion(
                    domain="food",
                    name="Mức phù hợp nhu cầu/khẩu vị",
                    direction="max",
                    weight=Decimal("0.3500"),
                ),
                DecisionCriterion(
                    domain="food",
                    name="Thời gian chuẩn bị",
                    direction="min",
                    weight=Decimal("0.2500"),
                ),
            ]
        if domain == "travel":
            return [
                DecisionCriterion(
                    domain="travel",
                    name="cost",
                    direction="min",
                    weight=Decimal("0.4000"),
                ),
                DecisionCriterion(
                    domain="travel",
                    name="duration",
                    direction="min",
                    weight=Decimal("0.3000"),
                ),
                DecisionCriterion(
                    domain="travel",
                    name="activities",
                    direction="max",
                    weight=Decimal("0.3000"),
                ),
            ]
        return []

    return rows


def _get_session_dialect_name(db: Session) -> str:
    """Trả về tên dialect SQLAlchemy viết thường (mysql, sqlite, ...), hoặc '' nếu là mock."""
    bind = getattr(db, "bind", None)
    if bind is None and hasattr(db, "get_bind"):
        try:
            bind = db.get_bind()
        except Exception:
            bind = None
    dialect = getattr(bind, "dialect", None)
    raw_name = getattr(dialect, "name", None)
    return raw_name.lower() if isinstance(raw_name, str) else ""


def _build_food_constraint_clause(
    field_name: str,
    operator: str,
    expected: Any,
    *,
    dialect_name: str,
) -> ColumnElement[bool] | None:
    """Chuyển một hard constraint sang biểu thức SQLAlchemy WHERE nếu đảm bảo tương đương 100%.

    Trả về None nếu điều kiện không phù hợp lọc ở SQL (để Engine lọc trong bộ nhớ).
    """
    if field_name in ("price", "prep_time"):
        col = Food.price if field_name == "price" else Food.prep_time
        guards = [col.is_not(None), col >= 0]

        if operator in ("in", "not_in"):
            values = _as_list(expected)
            if values is None:
                return None
            parsed = [_to_number(v) for v in values]
            if any(num is None for num in parsed):
                return None
            nums: list[Decimal | float] = [
                Decimal(str(v))
                if isinstance(v, (int, Decimal)) and not isinstance(v, bool)
                else float(num)
                for v, num in zip(values, parsed)
                if num is not None
            ]
            if not nums:
                return sa.false() if operator == "in" else sa.and_(*guards)
            cmp_expr = col.in_(nums) if operator == "in" else col.not_in(nums)
            return sa.and_(*guards, cmp_expr)

        num = _to_number(expected)
        if num is None:
            return None
        bound: Decimal | float = (
            Decimal(str(expected))
            if isinstance(expected, (int, Decimal)) and not isinstance(expected, bool)
            else num
        )
        if operator == "<=":
            return sa.and_(*guards, col <= bound)
        if operator == ">=":
            return sa.and_(*guards, col >= bound)
        if operator == "=":
            return sa.and_(*guards, col == bound)
        if operator == "!=":
            return sa.and_(*guards, col != bound)
        return None

    if field_name == "meal_type":
        norm_col = func.lower(func.trim(Food.meal_type))
        guards = [Food.meal_type.is_not(None), func.trim(Food.meal_type) != ""]

        if operator in ("in", "not_in"):
            values = _as_list(expected)
            if values is None:
                return None
            texts = [t for t in (_normalize_text(v) for v in values) if t]
            if not texts:
                return sa.false() if operator == "in" else sa.and_(*guards)
            if dialect_name == "sqlite" and not all(t.isascii() for t in texts):
                return None
            if dialect_name == "mysql" and not all(t.isascii() for t in texts):
                norm_expr: Any = norm_col.collate("utf8mb4_bin")
                target_vals: list[Any] = [sa.literal(t).collate("utf8mb4_bin") for t in texts]
            else:
                norm_expr = norm_col
                target_vals = texts
            cmp_expr = (
                norm_expr.in_(target_vals)
                if operator == "in"
                else norm_expr.not_in(target_vals)
            )
            return sa.and_(*guards, cmp_expr)

        text_val = _normalize_text(expected)
        if text_val is None:
            return None
        if dialect_name == "sqlite" and not text_val.isascii():
            return None
        if dialect_name == "mysql" and not text_val.isascii():
            norm_expr = norm_col.collate("utf8mb4_bin")
            target: Any = sa.literal(text_val).collate("utf8mb4_bin")
        else:
            norm_expr = norm_col
            target = text_val
        if operator == "=":
            return sa.and_(*guards, norm_expr == target)
        if operator == "!=":
            return sa.and_(*guards, norm_expr != target)
        return None

    if field_name == "ingredients":
        if dialect_name not in ("mysql", "sqlite") or operator not in ("in", "not_in"):
            return None
        values = _as_list(expected)
        if values is None:
            return None
        texts = [t for t in (_normalize_text(v) for v in values) if t]
        if not texts:
            return sa.true()
        if dialect_name == "sqlite" and not all(t.isascii() for t in texts):
            # SQLite LOWER() chỉ xử lý ASCII; giữ nguyên liệu Unicode lọc ở bộ nhớ.
            return None

        if dialect_name == "mysql":
            ing_norm: Any = func.lower(func.trim(Ingredient.name)).collate("utf8mb4_bin")
            empty_val: Any = sa.literal("").collate("utf8mb4_bin")
            t_exprs = [sa.literal(t).collate("utf8mb4_bin") for t in texts]
            any_match = sa.or_(
                *[
                    (func.locate(te, ing_norm) > 0) | (func.locate(ing_norm, te) > 0)
                    for te in t_exprs
                ]
            )
        else:
            ing_norm = func.lower(func.trim(Ingredient.name))
            empty_val = ""
            t_exprs = [sa.literal(t) for t in texts]
            any_match = sa.or_(
                *[
                    (func.instr(ing_norm, te) > 0) | (func.instr(te, ing_norm) > 0)
                    for te in t_exprs
                ]
            )

        ing_valid = sa.and_(Ingredient.name.is_not(None), ing_norm != empty_val)
        if operator == "not_in":
            return ~Food.ingredients.any(sa.and_(ing_valid, any_match))
        return ~Food.ingredients.any(sa.and_(ing_valid, ~any_match))

    return None


def filter_food_candidates_in_db(
    db: Session,
    constraints: dict[str, tuple[str, Any]] | None = None,
    *,
    excluded_limit: int = MAX_EXCLUDED_DETAIL,
) -> tuple[list[Food], list[Food], int, dict[str, tuple[str, Any]]] | None:
    """Lọc trước các hard constraint phù hợp ngay tại database.

    Trả về `(sql_matched_foods, sql_excluded_sample, sql_excluded_count, remaining_constraints)`
    hoặc `None` nếu bảng `foods` không có món ăn active nào (để Service fallback sang mock).
    """
    dialect_name = _get_session_dialect_name(db)
    if not dialect_name:
        rows = get_food_candidates(db)
        if not rows:
            return None
        return rows, [], 0, dict(constraints or {})

    sql_clauses: list[ColumnElement[bool]] = []
    remaining_constraints: dict[str, tuple[str, Any]] = {}
    for field_name, (operator, expected) in (constraints or {}).items():
        clause = _build_food_constraint_clause(
            field_name,
            operator,
            expected,
            dialect_name=dialect_name,
        )
        if clause is None:
            remaining_constraints[field_name] = (operator, expected)
        else:
            sql_clauses.append(clause)

    base_cond = sa.and_(Food.is_active.is_(True), Food.price >= 0)
    matched_load_opt = (
        selectinload(Food.ingredients)
        if "ingredients" in remaining_constraints
        else raiseload(Food.ingredients)
    )

    if not sql_clauses:
        rows = list(
            db.scalars(
                select(Food)
                .options(matched_load_opt)
                .where(base_cond)
                .order_by(Food.id.asc())
            ).all()
        )
        if not rows:
            return None
        return rows, [], 0, remaining_constraints

    combined_sql = sa.and_(*sql_clauses)
    stmt_valid = (
        select(Food)
        .options(matched_load_opt)
        .where(base_cond, combined_sql)
        .order_by(Food.id.asc())
    )
    sql_matched_foods = list(db.scalars(stmt_valid).all())

    # Dùng CASE để xử lý đúng 3-valued logic (NULL/UNKNOWN -> bị loại) của SQL.
    not_matched_sql = sa.case((combined_sql, sa.false()), else_=sa.true())
    sql_excluded_count = int(
        db.scalar(select(func.count(Food.id)).where(base_cond, not_matched_sql)) or 0
    )

    if not sql_matched_foods and sql_excluded_count == 0:
        return None

    sql_excluded_sample: list[Food] = []
    if sql_excluded_count > 0 and excluded_limit > 0:
        exc_load_opt = (
            selectinload(Food.ingredients)
            if (constraints and "ingredients" in constraints)
            else raiseload(Food.ingredients)
        )
        stmt_exc_sample = (
            select(Food)
            .options(exc_load_opt)
            .where(base_cond, not_matched_sql)
            .order_by(Food.id.asc())
            .limit(excluded_limit)
        )
        sql_excluded_sample = list(db.scalars(stmt_exc_sample).all())

    return sql_matched_foods, sql_excluded_sample, sql_excluded_count, remaining_constraints


def get_food_candidates(db: Session) -> list[Food]:
    """Truy vấn danh sách tất cả món ăn đang hoạt động từ bảng `foods`.

    Sử dụng selectinload để nạp trước danh sách nguyên liệu (ingredients),
    phục vụ cho việc kiểm tra hard constraint loại trừ nguyên liệu mà không gây N+1 query.

    Args:
        db: SQLAlchemy Session.

    Returns:
        list[Food]: Danh sách các món ăn thỏa điều kiện cơ bản (is_active=True, price>=0).
    """
    stmt = (
        select(Food)
        .options(selectinload(Food.ingredients))
        .where(Food.is_active.is_(True), Food.price >= 0)
        .order_by(Food.id.asc())
    )
    return list(db.scalars(stmt).all())


def get_food_criteria(db: Session) -> list[DecisionCriterion]:
    """Truy vấn danh sách tiêu chí đánh giá cho domain food từ DB."""
    return get_criteria_by_domain(db, domain="food")


def get_food_hard_constraints(db: Session) -> list[dict[str, str]]:
    """Truy vấn danh sách cấu hình điều kiện bắt buộc đang active cho domain food từ DB."""
    return get_hard_constraints_by_domain(db, domain="food")


def get_food_weights(db: Session) -> dict[str, float]:
    """Truy vấn trọng số các tiêu chí cho domain food từ DB."""
    return get_weights_by_domain(db, domain="food")


def get_travel_weights(db: Session) -> dict[str, float]:
    """Truy vấn trọng số các tiêu chí cho domain travel từ DB."""
    return get_weights_by_domain(db, domain="travel")


def create_decision(
    db: Session,
    *,
    user_id: int,
    domain: str,
    input_snapshot: dict[str, Any],
    result_snapshot: dict[str, Any],
) -> Decision:
    """Lưu một bản ghi lịch sử quyết định mới vào bảng `decisions`.

    Đảm bảo tính toàn vẹn giao dịch: nếu có lỗi khi ghi DB sẽ rollback ngay.
    """
    decision = Decision(
        user_id=user_id,
        domain=domain,
        input_snapshot=input_snapshot,
        result_snapshot=result_snapshot,
    )
    try:
        db.add(decision)
        db.commit()
        db.refresh(decision)
        return decision
    except Exception:
        db.rollback()
        raise


def get_decisions_by_user(
    db: Session,
    *,
    user_id: int,
    limit: int = 20,
    offset: int = 0,
) -> list[Decision]:
    """Lấy danh sách lịch sử quyết định của người dùng, sắp xếp mới nhất trước."""
    stmt = (
        select(Decision)
        .where(Decision.user_id == user_id)
        .order_by(Decision.created_at.desc(), Decision.id.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def count_decisions_by_user(db: Session, *, user_id: int) -> int:
    """Đếm tổng số bản ghi lịch sử quyết định của người dùng."""
    stmt = select(func.count(Decision.id)).where(Decision.user_id == user_id)
    return int(db.scalar(stmt) or 0)


def get_decision_by_id_and_user(
    db: Session,
    *,
    decision_id: int,
    user_id: int,
) -> Decision | None:
    """Truy vấn chi tiết một quyết định theo `decision_id` và `user_id`."""
    stmt = select(Decision).where(
        Decision.id == decision_id,
        Decision.user_id == user_id,
    )
    return db.scalar(stmt)



