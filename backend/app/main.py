"""Điểm khởi động của backend DecisionHub (Modular Monolith).

Chạy: uvicorn app.main:app --reload
Tài liệu Swagger: http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.common.exceptions import register_exception_handlers
from app.common.responses import success_response
from app.core.config import settings
from app.modules.auth.router import router as auth_router

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

# Khi module nghiệp vụ có router, đăng ký tại đây:
# from app.modules.food import router as food_router
# app.include_router(food_router.router, prefix="/api/v1/food", tags=["Food"])
app.include_router(auth_router)


@app.get("/health", summary="Kiểm tra sức khỏe hệ thống", tags=["Hệ thống"])
def health():
    return success_response({"app": settings.APP_NAME, "status": "ok"})
