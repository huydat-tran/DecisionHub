"""create_travel_places_table

Revision ID: e59757051dea
Revises: 1b04f303d588
Create Date: 2026-11-12 14:48:59.299700

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op # type: ignore[attr-defined]

# revision identifiers, used by Alembic.
revision: str = "e59757051dea"
down_revision: Union[str, Sequence[str], None] = "1b04f303d588"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

MYSQL_TABLE_ARGS = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}


def upgrade() -> None:
    """Tạo bảng travel_places với đầy đủ cột, ràng buộc và chỉ mục."""
    op.create_table(
        "travel_places",
        sa.Column(
            "id", sa.BigInteger(), autoincrement=True, nullable=False,
            comment="Khóa chính tự tăng định danh địa điểm",
        ),
        sa.Column(
            "name", sa.String(length=200), nullable=False,
            comment="Tên địa điểm du lịch",
        ),
        sa.Column(
            "province_city", sa.String(length=100), nullable=False,
            comment="Tỉnh hoặc Thành phố trực thuộc",
        ),
        sa.Column(
            "region",
            sa.Enum("Bắc", "Trung", "Nam", "Tây Nguyên", "Tây Nam Bộ", name="travelregion"),
            nullable=False,
            comment="Khu vực địa lý (Bắc, Trung, Nam, Tây Nguyên, Tây Nam Bộ)",
        ),
        sa.Column(
            "estimated_cost", sa.Integer(),
            server_default=sa.text("0"), nullable=False,
            comment="Chi phí tham khảo trung bình (VND) phục vụ lọc ngân sách và tính WSM Cost",
        ),
        sa.Column(
            "estimated_duration", sa.Numeric(precision=4, scale=1),
            server_default=sa.text("1.0"), nullable=False,
            comment="Thời lượng trải nghiệm ước tính (đơn vị: giờ)",
        ),
        sa.Column(
            "activity_type", sa.String(length=100), nullable=False,
            comment="Loại hình trải nghiệm chính (Nghỉ dưỡng biển, Khám phá thiên nhiên, Văn hóa lịch sử...)",
        ),
        sa.Column(
            "highlights", sa.Text(), nullable=True,
            comment="Danh sách hoạt động nổi bật, trải nghiệm đặc trưng (phân tách dấu phẩy hoặc dòng)",
        ),
        sa.Column(
            "description", sa.Text(), nullable=True,
            comment="Mô tả chi tiết về địa điểm",
        ),
        sa.Column(
            "image_url", sa.String(length=500), nullable=True,
            comment="URL ảnh minh họa (nếu thiếu, frontend dùng ảnh mặc định)",
        ),
        sa.Column(
            "rating", sa.Numeric(precision=2, scale=1),
            server_default=sa.text("4.5"), nullable=False,
            comment="Điểm đánh giá tham khảo (1.0 - 5.0)",
        ),
        sa.Column(
            "is_active", sa.Boolean(),
            server_default=sa.text("1"), nullable=False,
            comment="Trạng thái hoạt động (True: Đang mở cửa, False: Tạm ngưng)",
        ),
        sa.Column(
            "created_at", sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False,
            comment="Thời điểm tạo bản ghi",
        ),
        sa.Column(
            "updated_at", sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
            nullable=False,
            comment="Thời điểm cập nhật bản ghi",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_travel_places"),
        sa.UniqueConstraint("name", name="uq_travel_places_name"),
        **MYSQL_TABLE_ARGS,
    )

    # Chỉ mục đơn - phục vụ lọc nhanh từng tiêu chí (UC01 Quick Search)
    op.create_index("idx_travel_places_region", "travel_places", ["region"])
    op.create_index("idx_travel_places_cost", "travel_places", ["estimated_cost"])
    op.create_index("idx_travel_places_duration", "travel_places", ["estimated_duration"])
    op.create_index("idx_travel_places_activity_type", "travel_places", ["activity_type"])
    op.create_index("idx_travel_places_is_active", "travel_places", ["is_active"])

    # Chỉ mục tổng hợp - tối ưu Constraint Filtering trong Decision Engine (UC03)
    op.create_index(
        "idx_travel_places_composite_filter",
        "travel_places",
        ["region", "estimated_cost", "estimated_duration"],
    )


def downgrade() -> None:
    """Xóa bảng travel_places và toàn bộ chỉ mục liên quan."""
    op.drop_index("idx_travel_places_composite_filter", table_name="travel_places")
    op.drop_index("idx_travel_places_is_active", table_name="travel_places")
    op.drop_index("idx_travel_places_activity_type", table_name="travel_places")
    op.drop_index("idx_travel_places_duration", table_name="travel_places")
    op.drop_index("idx_travel_places_cost", table_name="travel_places")
    op.drop_index("idx_travel_places_region", table_name="travel_places")
    op.drop_table("travel_places")
