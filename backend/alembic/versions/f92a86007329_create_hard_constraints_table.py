"""create hard_constraints table

Revision ID: f92a86007329
Revises: b3f74c8eecf8
Create Date: 2026-11-12 09:47:06.721314

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f92a86007329"
down_revision: Union[str, Sequence[str], None] = "b3f74c8eecf8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

MYSQL_TABLE_ARGS = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}


def upgrade() -> None:
    """Tạo bảng hard_constraints."""
    op.create_table(
        "hard_constraints",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("domain", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("field_name", sa.String(length=50), nullable=False),
        sa.Column("operator", sa.String(length=20), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("1"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "domain IN ('food', 'travel')",
            name="ck_hard_constraints_domain",
        ),
        sa.CheckConstraint(
            "operator IN ('<=', '>=', '=', '!=', 'in', 'not_in')",
            name="ck_hard_constraints_operator",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_hard_constraints"),
        sa.UniqueConstraint(
            "domain",
            "name",
            name="uq_hard_constraints_domain_name",
        ),
        mysql_engine=MYSQL_TABLE_ARGS["mysql_engine"],
        mysql_charset=MYSQL_TABLE_ARGS["mysql_charset"],
        mysql_collate=MYSQL_TABLE_ARGS["mysql_collate"],
    )
    op.create_index(
        "idx_hard_constraints_domain_active",
        "hard_constraints",
        ["domain", "is_active"],
        unique=False,
    )


def downgrade() -> None:
    """Xóa bảng hard_constraints."""
    op.drop_index("idx_hard_constraints_domain_active", table_name="hard_constraints")
    op.drop_table("hard_constraints")
