"""Quản lý các Exception tùy chỉnh và xử lý lỗi chuẩn hóa cho DecisionHub."""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class DecisionHubException(Exception):
    """Exception gốc của hệ thống."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        data: dict | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.data = data or {}
        super().__init__(message)


class ResourceNotFoundException(DecisionHubException):
    """Lỗi không tìm thấy tài nguyên (404)."""

    def __init__(self, resource_name: str, resource_id: Any):
        super().__init__(
            message=f"{resource_name} với mã {resource_id} không tồn tại.",
            status_code=status.HTTP_404_NOT_FOUND,
            data={"resource": resource_name, "id": resource_id},
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Đăng ký các handler xử lý lỗi tùy chỉnh cho ứng dụng FastAPI."""

    @app.exception_handler(DecisionHubException)
    async def decision_hub_exception_handler(
        request: Request, exc: DecisionHubException
    ):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "detail": exc.message,
                "data": exc.data,
            },
        )
