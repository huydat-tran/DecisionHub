"""create decision_criteria table

Revision ID: b3f74c8eecf8
Revises: 1b04f303d588
Create Date: 2026-11-12 09:11:42.279316

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b3f74c8eecf8"
down_revision: Union[str, Sequence[str], None] = "1b04f303d588"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

MYSQL_TABLE_ARGS = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}


def upgrade() -> None:
    """Tạo bảng decision_criteria."""
    op.create_table(
        "decision_criteria",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("direction", sa.String(length=10), nullable=False),
        sa.Column("weight", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.CheckConstraint(
            "direction IN ('min', 'max')",
            name="ck_decision_criteria_direction",
        ),
        sa.CheckConstraint(
            "weight >= 0 AND weight <= 1",
            name="ck_decision_criteria_weight",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_decision_criteria"),
        sa.UniqueConstraint("name", name="uq_decision_criteria_name"),
        mysql_engine=MYSQL_TABLE_ARGS["mysql_engine"],
        mysql_charset=MYSQL_TABLE_ARGS["mysql_charset"],
        mysql_collate=MYSQL_TABLE_ARGS["mysql_collate"],
    )


def downgrade() -> None:
    """Xóa bảng decision_criteria."""
    op.drop_table("decision_criteria")
