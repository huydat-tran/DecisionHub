"""Quản lý kết nối MySQL và Database Session bằng SQLAlchemy 2.x.

Cung cấp engine, SessionLocal, Base và dependency get_db() dùng chung cho toàn dự án.
"""

from collections.abc import Generator
import logging
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

# Engine kết nối cơ sở dữ liệu (dùng chung toàn dự án)
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Phiên làm việc (dùng chung toàn dự án)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    """Lớp cơ sở cho toàn bộ SQLAlchemy models trong hệ thống."""


def get_db() -> Generator[Session, None, None]:
    """Dependency cung cấp Session cho FastAPI routes, tự động đóng sau khi hoàn tất."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_database_exists() -> None:
    """Tạo database nếu chưa có (bảng thì do Alembic lo)."""
    db_name = settings.DB_NAME
    if not db_name.replace("_", "").isalnum():
        raise ValueError(f"DB_NAME không hợp lệ: {db_name}")

    server_engine = create_engine(settings.server_database_url, isolation_level="AUTOCOMMIT")
    try:
        with server_engine.connect() as conn:
            conn.execute(
                text(
                    f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            )
    finally:
        server_engine.dispose()
    logger.info("Database '%s' đã sẵn sàng.", db_name)


def init_database() -> None:
    """Khởi tạo cấu trúc bảng khi chạy ứng dụng.

    Dùng Alembic làm nguồn chuẩn: các bảng đã tồn tại được giữ nguyên, chỉ tạo phần còn thiếu.
    """
    _ensure_database_exists()

    from alembic import command
    from alembic.config import Config

    alembic_dir = Path(__file__).resolve().parent.parent.parent / "alembic"
    cfg = Config(str(alembic_dir.parent / "alembic.ini"))
    cfg.set_main_option("script_location", str(alembic_dir))

    command.upgrade(cfg, "head")
    logger.info("Cấu trúc bảng đã được cập nhật (Alembic upgrade head).")
