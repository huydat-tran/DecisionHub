"""create_foods_and_ingredients_tables

Revision ID: c7a1d4e9f201
Revises: b9f2129b7ec8
Create Date: 2026-11-13 22:52:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c7a1d4e9f201"
down_revision: Union[str, Sequence[str], None] = "b9f2129b7ec8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

MYSQL_TABLE_ARGS = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}


def upgrade() -> None:
    """Tạo bảng ingredients, foods và bảng trung gian food_ingredients."""
    op.create_table(
        "ingredients",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_ingredients"),
        **MYSQL_TABLE_ARGS,
    )
    op.create_index("ix_ingredients_id", "ingredients", ["id"], unique=False)
    op.create_index("ix_ingredients_name", "ingredients", ["name"], unique=True)

    op.create_table(
        "foods",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("meal_type", sa.String(length=50), nullable=False),
        sa.Column("prep_time", sa.Integer(), nullable=True),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint("price >= 0", name="check_food_price_non_negative"),
        sa.CheckConstraint("prep_time >= 0", name="check_prep_time_non_negative"),
        sa.PrimaryKeyConstraint("id", name="pk_foods"),
        **MYSQL_TABLE_ARGS,
    )
    op.create_index("ix_foods_id", "foods", ["id"], unique=False)
    op.create_index("ix_foods_name", "foods", ["name"], unique=False)
    op.create_index("ix_foods_meal_type", "foods", ["meal_type"], unique=False)

    op.create_table(
        "food_ingredients",
        sa.Column("food_id", sa.Integer(), nullable=False),
        sa.Column("ingredients_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["food_id"],
            ["foods.id"],
            name="fk_food_ingredients_food_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["ingredients_id"],
            ["ingredients.id"],
            name="fk_food_ingredients_ingredients_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("food_id", "ingredients_id", name="pk_food_ingredients"),
        **MYSQL_TABLE_ARGS,
    )


def downgrade() -> None:
    """Xóa bảng food_ingredients, foods và ingredients."""
    op.drop_table("food_ingredients")
    op.drop_index("ix_foods_meal_type", table_name="foods")
    op.drop_index("ix_foods_name", table_name="foods")
    op.drop_index("ix_foods_id", table_name="foods")
    op.drop_table("foods")
    op.drop_index("ix_ingredients_name", table_name="ingredients")
    op.drop_index("ix_ingredients_id", table_name="ingredients")
    op.drop_table("ingredients")
