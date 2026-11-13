"""add domain to decision_criteria

Revision ID: a8c31f6e4d20
Revises: b9f2129b7ec8
Create Date: 2026-11-13 23:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a8c31f6e4d20"
down_revision: Union[str, Sequence[str], None] = "b9f2129b7ec8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Thêm domain cho decision_criteria, giữ nguyên tiêu chí Food hiện có.

    Mọi bản ghi đã tồn tại thuộc rubric Food (chưa có tiêu chí Travel),
    nên được gán domain = 'food' trước khi cột thành NOT NULL.
    Unique trên name được thay bằng unique (domain, name).
    """
    op.add_column(
        "decision_criteria",
        sa.Column("domain", sa.String(length=20), nullable=True),
    )
    op.execute(
        "UPDATE decision_criteria SET domain = 'food' WHERE domain IS NULL"
    )
    op.alter_column(
        "decision_criteria",
        "domain",
        existing_type=sa.String(length=20),
        existing_nullable=True,
        nullable=False,
    )
    op.drop_constraint(
        "uq_decision_criteria_name",
        "decision_criteria",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_decision_criteria_domain_name",
        "decision_criteria",
        ["domain", "name"],
    )
    op.create_check_constraint(
        "ck_decision_criteria_domain",
        "decision_criteria",
        "domain IN ('food', 'travel')",
    )


def downgrade() -> None:
    """Gỡ domain và khôi phục unique trên name.

    Xóa tiêu chí travel trước khi bỏ cột domain để dữ liệu còn lại
    vẫn thỏa unique(name) của schema cũ.
    """
    op.execute("DELETE FROM decision_criteria WHERE domain = 'travel'")
    op.drop_constraint(
        "ck_decision_criteria_domain",
        "decision_criteria",
        type_="check",
    )
    op.drop_constraint(
        "uq_decision_criteria_domain_name",
        "decision_criteria",
        type_="unique",
    )
    op.drop_column("decision_criteria", "domain")
    op.create_unique_constraint(
        "uq_decision_criteria_name",
        "decision_criteria",
        ["name"],
    )
