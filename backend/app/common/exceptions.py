"""Quản lý các Exception tùy chỉnh và xử lý lỗi chuẩn hóa cho DecisionHub.

Mọi response lỗi đều có cùng cấu trúc 6 trường:
    success, message, data, error_code, errors, path
"""

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

# Mã lỗi mặc định theo HTTP status code.
ERROR_CODE_BY_STATUS: dict[int, str] = {
    status.HTTP_400_BAD_REQUEST: "BAD_REQUEST",
    status.HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
    status.HTTP_403_FORBIDDEN: "FORBIDDEN",
    status.HTTP_404_NOT_FOUND: "NOT_FOUND",
    status.HTTP_405_METHOD_NOT_ALLOWED: "METHOD_NOT_ALLOWED",
    status.HTTP_409_CONFLICT: "CONFLICT",
    status.HTTP_422_UNPROCESSABLE_ENTITY: "VALIDATION_ERROR",
    status.HTTP_500_INTERNAL_SERVER_ERROR: "INTERNAL_SERVER_ERROR",
    status.HTTP_503_SERVICE_UNAVAILABLE: "SERVICE_UNAVAILABLE",
}


def default_error_code(status_code: int) -> str:
    """Suy ra error_code ổn định từ HTTP status code."""
    return ERROR_CODE_BY_STATUS.get(status_code, "ERROR")


def build_error_response(
    request: Request,
    status_code: int,
    message: str,
    error_code: str,
    data: Any = None,
    errors: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    """Dựng response lỗi theo cấu trúc thống nhất của dự án."""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": message,
            "data": data,
            "error_code": error_code,
            "errors": errors,
            "path": request.url.path,
        },
    )


class DecisionHubException(Exception):
    """Exception gốc của hệ thống."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        data: Any = None,
        error_code: str | None = None,
        errors: list[dict[str, Any]] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.data = data
        self.error_code = error_code or default_error_code(status_code)
        self.errors = errors
        super().__init__(message)


class ResourceNotFoundException(DecisionHubException):
    """Lỗi không tìm thấy tài nguyên (404)."""

    def __init__(self, resource_name: str, resource_id: Any):
        super().__init__(
            message=f"{resource_name} với mã {resource_id} không tồn tại.",
            status_code=status.HTTP_404_NOT_FOUND,
            data={"resource": resource_name, "id": resource_id},
            error_code="RESOURCE_NOT_FOUND",
        )


class BadRequestException(DecisionHubException):
    """Lỗi request không hợp lệ (400)."""

    def __init__(self, message: str, data: Any = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            data=data,
            error_code="BAD_REQUEST",
        )


class UnauthorizedException(DecisionHubException):
    """Lỗi chưa xác thực hoặc token không hợp lệ (401)."""

    def __init__(self, message: str, data: Any = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            data=data,
            error_code="UNAUTHORIZED",
        )


class ForbiddenException(DecisionHubException):
    """Lỗi đã xác thực nhưng không đủ quyền (403)."""

    def __init__(self, message: str, data: Any = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            data=data,
            error_code="FORBIDDEN",
        )


class NotFoundException(DecisionHubException):
    """Lỗi không tìm thấy tài nguyên (404) dùng cho message tuỳ biến."""

    def __init__(self, message: str, data: Any = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            data=data,
            error_code="NOT_FOUND",
        )


class UnprocessableEntityException(DecisionHubException):
    """Lỗi dữ liệu đầu vào không vượt qua validation (422)."""

    def __init__(self, message: str, errors: list[dict[str, Any]] | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            errors=errors,
        )


def _serialize_validation_errors(exc: RequestValidationError) -> list[dict[str, Any]]:
    """Chuyển lỗi validation của Pydantic sang dạng JSON serialize được."""
    errors: list[dict[str, Any]] = []
    for error in exc.errors():
        loc = error.get("loc") or ()
        field = ".".join(str(part) for part in loc)
        errors.append(
            {
                "field": field,
                "message": error.get("msg", "Giá trị không hợp lệ."),
            }
        )
    return errors


def register_exception_handlers(app: FastAPI) -> None:
    """Đăng ký các handler xử lý lỗi chuẩn hóa cho ứng dụng FastAPI."""

    @app.exception_handler(DecisionHubException)
    async def decision_hub_exception_handler(
        request: Request, exc: DecisionHubException
    ):
        return build_error_response(
            request=request,
            status_code=exc.status_code,
            message=exc.message,
            error_code=exc.error_code,
            data=exc.data,
            errors=exc.errors,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ):
        detail = exc.detail
        message = detail if isinstance(detail, str) else "Đã xảy ra lỗi HTTP."
        data = None if isinstance(detail, str) else detail
        return build_error_response(
            request=request,
            status_code=exc.status_code,
            message=message,
            error_code=default_error_code(exc.status_code),
            data=data,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        return build_error_response(
            request=request,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="Dữ liệu đầu vào không hợp lệ",
            error_code="VALIDATION_ERROR",
            errors=_serialize_validation_errors(exc),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Lỗi không mong muốn tại %s", request.url.path)
        return build_error_response(
            request=request,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Đã xảy ra lỗi không mong muốn. Vui lòng thử lại sau.",
            error_code="INTERNAL_SERVER_ERROR",
        )
