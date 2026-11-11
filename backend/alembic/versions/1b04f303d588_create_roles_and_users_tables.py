"""create roles and users tables

Revision ID: 1b04f303d588
Revises:
Create Date: 2026-11-11 22:33:37.424337

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1b04f303d588"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

MYSQL_TABLE_ARGS = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}


def upgrade() -> None:
    """Tạo bảng roles và users."""
    op.create_table(
        "roles",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=20), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_roles"),
        sa.UniqueConstraint("name", name="uq_roles_name"),
        mysql_engine=MYSQL_TABLE_ARGS["mysql_engine"],
        mysql_charset=MYSQL_TABLE_ARGS["mysql_charset"],
        mysql_collate=MYSQL_TABLE_ARGS["mysql_collate"],
    )
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
            name="fk_users_role",
            onupdate="CASCADE",
            ondelete="RESTRICT",
        ),
        mysql_engine=MYSQL_TABLE_ARGS["mysql_engine"],
        mysql_charset=MYSQL_TABLE_ARGS["mysql_charset"],
        mysql_collate=MYSQL_TABLE_ARGS["mysql_collate"],
    )
    op.create_index("idx_users_role_id", "users", ["role_id"])


def downgrade() -> None:
    """Xóa bảng users và roles."""
    op.drop_index("idx_users_role_id", table_name="users")
    op.drop_table("users")
    op.drop_table("roles")
