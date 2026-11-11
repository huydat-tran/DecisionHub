"""Điểm khởi động của backend DecisionHub (Modular Monolith).

Chạy: uvicorn app.main:app --reload
Tài liệu Swagger: http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.common.exceptions import register_exception_handlers
from app.common.responses import success_response
from app.core.config import settings
from app.core.database import Base, engine
from app.modules.items import models as items_models  # noqa: F401
from app.modules.items import router as items_router

# Tự động tạo các bảng database nếu chưa tồn tại
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="Hệ thống hỗ trợ ra quyết định DecisionHub - API Backend",
    version="1.0.0",
)

# Đăng ký xử lý lỗi chuẩn hóa
register_exception_handlers(app)

# CORS: cho phép Frontend gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký các router nghiệp vụ
app.include_router(items_router.router, prefix="/api/items", tags=["Items"])


@app.get(
    "/api/health",
    summary="Kiểm tra kết nối Frontend -> Backend -> MySQL",
    tags=["Hệ thống"],
)
def api_health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"app": settings.APP_NAME, "status": "ok", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Lỗi kết nối MySQL: {e}",
        )


@app.get("/health", summary="Kiểm tra sức khỏe hệ thống", tags=["Hệ thống"])
def health():
    return success_response({"app": settings.APP_NAME, "status": "ok"})

