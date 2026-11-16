"""SQLAlchemy models cho module Decision.

Dùng chung Base từ app.core.database để Alembic và SQLAlchemy nhận diện metadata.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

DECISION_DOMAINS = ("food", "travel")


class DecisionCriterion(Base):
    """Tiêu chí đánh giá dùng chung cho Food và Travel.

    Cặp (domain, name) là duy nhất. `direction` cho biết chiều tối ưu khi
    chuẩn hóa (min hoặc max). Engine đọc direction từ dữ liệu, không gắn
    cứng chiều cho từng tiêu chí.
    """

    __tablename__ = "decision_criteria"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    domain: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    weight: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)

    __table_args__ = (
        UniqueConstraint("domain", "name", name="uq_decision_criteria_domain_name"),
        CheckConstraint(
            "domain IN ('food', 'travel')",
            name="ck_decision_criteria_domain",
        ),
        CheckConstraint(
            "direction IN ('min', 'max')",
            name="ck_decision_criteria_direction",
        ),
        CheckConstraint(
            "weight >= 0 AND weight <= 1",
            name="ck_decision_criteria_weight",
        ),
    )


class HardConstraint(Base):
    """Cấu hình điều kiện bắt buộc (hard constraint) để lọc ứng viên trước khi chấm điểm."""

    __tablename__ = "hard_constraints"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    domain: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    field_name: Mapped[str] = mapped_column(String(50), nullable=False)
    operator: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("1"),
    )

    __table_args__ = (
        UniqueConstraint("domain", "name", name="uq_hard_constraints_domain_name"),
        CheckConstraint(
            "domain IN ('food', 'travel')",
            name="ck_hard_constraints_domain",
        ),
        CheckConstraint(
            "operator IN ('<=', '>=', '=', '!=', 'in', 'not_in')",
            name="ck_hard_constraints_operator",
        ),
        Index("idx_hard_constraints_domain_active", "domain", "is_active"),
    )


class DecisionResult(Base):
    """Kết quả gợi ý và chấm điểm của từng phương án (Food hoặc Travel) trong một phiên quyết định.

    Sử dụng mô hình Exclusive Arc:
    - Nếu quyết định về Food: `food_id` có giá trị, `travel_id` là NULL.
    - Nếu quyết định về Travel: `travel_id` có giá trị, `food_id` là NULL.
    """

    __tablename__ = "decision_results"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="Khóa chính tự tăng của kết quả quyết định",
    )
    decision_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="ID phiên quyết định (sẽ liên kết FK với decisions(id) sau)",
    )
    food_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        default=None,
        comment="ID món ăn (sẽ liên kết FK với foods(id) sau); NULL nếu là kết quả travel",
    )
    travel_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        default=None,
        comment="ID địa điểm du lịch; NULL nếu là kết quả food",
    )
    total_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Tổng điểm WSM đã chuẩn hóa (0.00 - 100.00)",
    )
    rank: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Thứ hạng sau khi chấm điểm và áp dụng tie-breaker (1, 2, ...)",
    )
    score_details: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment="Chi tiết điểm từng tiêu chí (JSON: price, preference, prep_time, reasons...)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        comment="Thời điểm ghi nhận kết quả",
    )

    __table_args__ = (
        UniqueConstraint(
            "decision_id", "rank", name="uq_decision_results_decision_rank"
        ),
        UniqueConstraint(
            "decision_id", "food_id", name="uq_decision_results_decision_food"
        ),
        UniqueConstraint(
            "decision_id", "travel_id", name="uq_decision_results_decision_travel"
        ),
        CheckConstraint(
            "(food_id IS NOT NULL AND travel_id IS NULL) OR (food_id IS NULL AND travel_id IS NOT NULL)",
            name="ck_decision_results_target",
        ),
        CheckConstraint(
            "total_score >= 0 AND total_score <= 100",
            name="ck_decision_results_total_score",
        ),
        CheckConstraint("`rank` >= 1", name="ck_decision_results_rank"),
        Index("idx_decision_results_decision_id", "decision_id"),
        Index("idx_decision_results_food_id", "food_id"),
        Index("idx_decision_results_travel_id", "travel_id"),
        Index("idx_decision_results_decision_rank", "decision_id", "rank"),
    )
