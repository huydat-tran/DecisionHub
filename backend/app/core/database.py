"""Quản lý kết nối MySQL và Database Session bằng SQLAlchemy 2.x.

Cung cấp engine, SessionLocal, Base và dependency get_db() dùng chung cho toàn dự án.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

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
