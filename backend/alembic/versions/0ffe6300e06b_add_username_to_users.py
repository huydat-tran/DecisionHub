"""add username to users

Revision ID: 0ffe6300e06b
Revises: e59757051dea
Create Date: 2026-11-12 19:46:05.954389

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op # type: ignore[attr-defined]

# revision identifiers, used by Alembic.
revision: str = "0ffe6300e06b"
down_revision: Union[str, Sequence[str], None] = "e59757051dea"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Thêm cột username (UNIQUE) cho bảng users.

    Cột được thêm nullable trước để backfill giá trị cho các bản ghi sẵn có,
    sau đó mới chuyển sang NOT NULL và tạo unique constraint.
    """
    op.add_column("users", sa.Column("username", sa.String(length=50), nullable=True))
    op.execute("UPDATE users SET username = CONCAT('legacy_user_', id) WHERE username IS NULL")
    op.alter_column("users", "username", nullable=False)
    op.create_unique_constraint("uq_users_username", "users", ["username"])


def downgrade() -> None:
    """Xóa cột username và ràng buộc unique tương ứng."""
    op.drop_constraint("uq_users_username", "users", type_="unique")
    op.drop_column("users", "username")
