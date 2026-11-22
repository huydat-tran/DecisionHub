"""create_decisions_table

Revision ID: d4e8a9c12b34
Revises: a8c31f6e4d20, c7a1d4e9f201
Create Date: 2026-11-22 13:09:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e8a9c12b34"
down_revision: str | Sequence[str] | None = ("a8c31f6e4d20", "c7a1d4e9f201")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MYSQL_TABLE_ARGS = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}


def upgrade() -> None:
    """Tạo bảng decisions lưu lịch sử các phiên quyết định của người dùng."""
    op.create_table(
        "decisions",
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
            comment="Khóa chính tự tăng định danh phiên quyết định",
        ),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            nullable=False,
            comment="ID người dùng thực hiện quyết định (FK -> users.id)",
        ),
        sa.Column(
            "domain",
            sa.String(length=20),
            nullable=False,
            comment="Phân loại miền quyết định: food (ăn uống) hoặc travel (du lịch)",
        ),
        sa.Column(
            "input_snapshot",
            sa.JSON(),
            nullable=False,
            comment="Snapshot JSON toàn bộ dữ liệu đầu vào tại thời điểm đề xuất",
        ),
        sa.Column(
            "result_snapshot",
            sa.JSON(),
            nullable=False,
            comment="Snapshot JSON kết quả đề xuất (danh sách phương án xếp hạng, điểm số, lý do giải thích)",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="Thời điểm tạo quyết định",
        ),
        sa.CheckConstraint(
            "domain IN ('food', 'travel')",
            name="ck_decisions_domain",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_decisions_user",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_decisions"),
        **MYSQL_TABLE_ARGS,
    )
    op.create_index(
        "idx_decisions_user_id",
        "decisions",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "idx_decisions_user_created_at",
        "decisions",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "idx_decisions_user_domain_created_at",
        "decisions",
        ["user_id", "domain", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Xóa bảng decisions và các chỉ mục liên quan."""
    op.drop_index("idx_decisions_user_domain_created_at", table_name="decisions")
    op.drop_index("idx_decisions_user_created_at", table_name="decisions")
    op.drop_index("idx_decisions_user_id", table_name="decisions")
    op.drop_table("decisions")
