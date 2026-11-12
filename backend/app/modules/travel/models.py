"""SQLAlchemy models cho module Travel (Địa điểm du lịch).

Phù hợp với Use Case DecisionHub Travel:
- UC01: Quick Search (Tìm kiếm theo keyword, lọc theo chip nhanh: khu vực, ngân sách, thời lượng, loại hình).
- UC02: View Detail (Xem chi tiết địa điểm, mô tả, chi phí tham khảo, thời lượng, hoạt động nổi bật).
- UC03: Smart Recommendation (Lọc điều kiện cứng ngân sách, thời lượng, khu vực; chấm điểm WSM; tie-breaker).
"""

from datetime import datetime
from decimal import Decimal
import enum

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum as SAEnum,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TravelRegion(str, enum.Enum):
    """Khu vực địa lý của địa điểm du lịch, phục vụ bộ lọc nhanh và Decision Engine."""

    BAC = "Bắc"
    TRUNG = "Trung"
    NAM = "Nam"
    TAY_NGUYEN = "Tây Nguyên"
    TAY_NAM_BO = "Tây Nam Bộ"


class TravelPlace(Base):
    """Mô hình dữ liệu lưu trữ địa điểm du lịch (Travel Place).

    Tương ứng với bảng `travel_places` trong CSDL MySQL.
    """

    __tablename__ = "travel_places"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="Khóa chính tự tăng định danh địa điểm",
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        unique=True,
        comment="Tên địa điểm du lịch",
    )
    province_city: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Tỉnh hoặc Thành phố trực thuộc",
    )
    region: Mapped[TravelRegion] = mapped_column(
        SAEnum(TravelRegion, values_callable=lambda x: [e.value for e in x], native_enum=True),
        nullable=False,
        comment="Khu vực địa lý (Bắc, Trung, Nam, Tây Nguyên, Tây Nam Bộ)",
    )
    estimated_cost: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="Chi phí tham khảo trung bình (VND) phục vụ lọc ngân sách và tính WSM Cost",
    )
    estimated_duration: Mapped[Decimal] = mapped_column(
        Numeric(4, 1),
        nullable=False,
        default=Decimal("1.0"),
        server_default=text("1.0"),
        comment="Thời lượng trải nghiệm ước tính (đơn vị: giờ)",
    )
    activity_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Loại hình trải nghiệm chính (Nghỉ dưỡng biển, Khám phá thiên nhiên, Văn hóa lịch sử...)",
    )
    highlights: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Danh sách hoạt động nổi bật, trải nghiệm đặc trưng (phân tách dấu phẩy hoặc dòng)",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Mô tả chi tiết về địa điểm",
    )
    image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="URL ảnh minh họa (nếu thiếu, frontend dùng ảnh mặc định)",
    )
    rating: Mapped[Decimal] = mapped_column(
        Numeric(2, 1),
        nullable=False,
        default=Decimal("4.5"),
        server_default=text("4.5"),
        comment="Điểm đánh giá tham khảo (1.0 - 5.0)",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("1"),
        comment="Trạng thái hoạt động (True: Đang mở cửa, False: Tạm ngưng)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        comment="Thời điểm tạo bản ghi",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        comment="Thời điểm cập nhật bản ghi",
    )

    __table_args__ = (
        Index("idx_travel_places_region", "region"),
        Index("idx_travel_places_cost", "estimated_cost"),
        Index("idx_travel_places_duration", "estimated_duration"),
        Index("idx_travel_places_activity_type", "activity_type"),
        Index("idx_travel_places_is_active", "is_active"),
        Index("idx_travel_places_composite_filter", "region", "estimated_cost", "estimated_duration"),
    )

    @property
    def highlights_list(self) -> list[str]:
        """Tách chuỗi highlights thành danh sách hoạt động phục vụ hiển thị chi tiết (UC02)."""
        if not self.highlights:
            return []
        # Hỗ trợ phân tách bằng dấu phẩy hoặc xuống dòng
        items = [item.strip() for item in self.highlights.replace("\n", ",").split(",") if item.strip()]
        return items

    def __repr__(self) -> str:
        return f"<TravelPlace id={self.id} name='{self.name}' region='{self.region}' cost={self.estimated_cost}>"


# Alias để tương thích nếu các module khác gọi tên Destination
Destination = TravelPlace
