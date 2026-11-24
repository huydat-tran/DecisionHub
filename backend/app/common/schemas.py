"""Pydantic schemas dùng chung cho nhiều module.

Hiện chỉ có cấu trúc response lỗi thống nhất của dự án, dùng để mô tả
các error response trong tài liệu OpenAPI/Swagger.
"""

from typing import Any

from pydantic import BaseModel, Field


class ValidationErrorDetail(BaseModel):
    """Chi tiết một lỗi validation của request."""

    field: str = Field(..., description="Tên trường bị lỗi.")
    message: str = Field(..., description="Thông báo mô tả lỗi.")


class ErrorResponse(BaseModel):
    """Response lỗi thống nhất của dự án (dùng trong tài liệu OpenAPI)."""

    success: bool = Field(False, description="Luôn là false khi có lỗi.")
    message: str = Field(..., description="Thông báo lỗi dễ hiểu cho người dùng.")
    data: Any = Field(None, description="Dữ liệu bổ sung (thường là null).")
    error_code: str = Field(..., description="Mã lỗi ổn định để xử lý phía client.")
    errors: list[ValidationErrorDetail] | None = Field(
        None, description="Danh sách lỗi chi tiết khi lỗi do validation dữ liệu đầu vào."
    )
    path: str = Field(..., description="Đường dẫn API sinh ra lỗi.")
