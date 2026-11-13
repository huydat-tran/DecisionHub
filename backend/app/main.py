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
from app.modules.food.router_food import router as food_router
from app.modules.users.router import router as users_router

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

# Đăng ký router cho các module nghiệp vụ
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(food_router)


@app.get("/health", summary="Kiểm tra sức khỏe hệ thống", tags=["Hệ thống"])
def health():
    return success_response({"app": settings.APP_NAME, "status": "ok"})
