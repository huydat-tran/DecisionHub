"""SQLAlchemy models cho module Decision.

Dùng chung Base từ app.core.database để Alembic và SQLAlchemy nhận diện metadata.
"""

from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DecisionCriterion(Base):
    """Tiêu chí đánh giá dùng trong thuật toán tính điểm quyết định."""

    __tablename__ = "decision_criteria"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    weight: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)

    __table_args__ = (
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
