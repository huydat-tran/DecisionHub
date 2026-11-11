"""Định dạng response dùng chung cho toàn dự án.

Hiện tại chỉ cần một cấu trúc thống nhất cho response thành công.
Các format lỗi được xử lý tại app/common/exceptions.py.
"""

from typing import Any


def success_response(data: Any = None, message: str = "OK") -> dict[str, Any]:
    """Bọc dữ liệu thành công vào cấu trúc response thống nhất."""
    return {"success": True, "message": message, "data": data}
