"""Helper dùng chung để khai báo error response trong tài liệu OpenAPI.

Format lỗi thống nhất của dự án được xử lý tại app/common/exceptions.py.
"""

from typing import Any

from app.common.schemas import ErrorResponse

# Kiểu responses mà FastAPI chấp nhận cho decorator (Dict[Union[int, str], ...]).
ResponsesDict = dict[int | str, dict[str, Any]]


def error_example(
    message: str,
    error_code: str,
    path: str,
    errors: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Dựng ví dụ JSON response lỗi theo format thống nhất của dự án.

    Lưu ý: FastAPI loại bỏ các giá trị null khi sinh OpenAPI (exclude_none),
    nên trên Swagger UI các trường `data`/`errors` có giá trị null sẽ không hiển thị.
    """
    return {
        "success": False,
        "message": message,
        "data": None,
        "error_code": error_code,
        "errors": errors,
        "path": path,
    }


def error_response(description: str, example: dict[str, Any]) -> dict[str, Any]:
    """Dựng entry error response cho tham số `responses` của FastAPI."""
    return {
        "model": ErrorResponse,
        "description": description,
        "content": {"application/json": {"example": example}},
    }
