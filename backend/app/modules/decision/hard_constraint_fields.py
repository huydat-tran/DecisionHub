"""Cấu hình field và operator cho HardConstraint (điều kiện bắt buộc), theo domain.

Tách riêng khỏi `criterion_fields.py` vì hai nghiệp vụ khác nhau:
- `criterion_fields.py`: ánh xạ field phục vụ chấm điểm (DecisionCriterion).
- `hard_constraint_fields.py`: quản lý field + operator phục vụ lọc ứng viên.

Cấu hình được chia theo domain: mỗi domain có danh sách field (kèm kiểu dữ liệu),
ánh xạ tên field trong Request → field của constraint, và operator mặc định khi
chuyển tham số Request cũ. Thêm domain mới chỉ cần bổ sung cấu hình, không phải
viết lại cơ chế validation hay operator dispatch.

Module này thuần Python: không truy vấn database, không thực thi biểu thức động.
"""

from typing import Any

# Operator được Database cho phép (dùng chung cho mọi domain).
SUPPORTED_OPERATORS: frozenset[str] = frozenset({"<=", ">=", "=", "!=", "in", "not_in"})

# Operator hợp lệ theo từng kiểu field (dùng để báo lỗi cấu hình rõ ràng).
OPERATORS_BY_KIND: dict[str, frozenset[str]] = {
    "number": frozenset(SUPPORTED_OPERATORS),
    "text": frozenset({"=", "!=", "in", "not_in"}),
    "list": frozenset({"in", "not_in"}),
}

# Domain dùng khi caller không chỉ định (tương thích ngược cho Engine).
DEFAULT_DOMAIN: str = "food"

# Cấu hình HardConstraint của từng domain.
# - "fields": field của ứng viên → kiểu dữ liệu quyết định cách so sánh.
# - "request_mapping": tên field trong Request → field_name của HardConstraint.
# - "default_operators": operator mặc định dùng khi chuyển tham số Request cũ.
DOMAIN_CONSTRAINT_CONFIG: dict[str, dict[str, Any]] = {
    "food": {
        "fields": {
            "price": "number",
            "meal_type": "text",
            "prep_time": "number",
            "ingredients": "list",
        },
        "request_mapping": {
            "budget_max": "price",
            "meal_type": "meal_type",
            "max_prep_time": "prep_time",
            "excluded_ingredients": "ingredients",
        },
        "default_operators": {
            "price": "<=",
            "meal_type": "=",
            "prep_time": "<=",
            "ingredients": "not_in",
        },
    },
}


def get_domain_constraint_config(domain: str) -> dict[str, Any]:
    """Lấy cấu hình HardConstraint của một domain.

    Args:
        domain: Tên domain ("food", ...).

    Returns:
        dict: Cấu hình gồm "fields", "request_mapping", "default_operators".

    Raises:
        ValueError: Khi domain chưa có cấu hình.
    """
    config = DOMAIN_CONSTRAINT_CONFIG.get(domain)
    if config is None:
        raise ValueError(
            f"Domain chưa có cấu hình HardConstraint: {domain!r}. "
            f"Các domain hợp lệ: {sorted(DOMAIN_CONSTRAINT_CONFIG)}."
        )
    return config


def get_supported_fields(domain: str) -> frozenset[str]:
    """Lấy tập field được phép dùng làm điều kiện lọc của `domain`."""
    return frozenset(get_domain_constraint_config(domain)["fields"])


def get_request_field_mapping(domain: str) -> dict[str, str]:
    """Lấy ánh xạ tên field trong Request → field_name của HardConstraint."""
    return dict(get_domain_constraint_config(domain)["request_mapping"])


def get_default_operators(domain: str) -> dict[str, str]:
    """Lấy operator mặc định theo field của `domain`.

    Dùng khi chuyển tham số Request cũ (budget_max, meal_type, ...) thành cấu
    hình constraints.
    """
    return dict(get_domain_constraint_config(domain)["default_operators"])


def get_field_kind(domain: str, field_name: str) -> str:
    """Lấy kiểu dữ liệu của `field_name` trong `domain`.

    Raises:
        ValueError: Khi domain không có cấu hình hoặc field không thuộc domain.
    """
    fields = get_domain_constraint_config(domain)["fields"]
    kind = fields.get(field_name)
    if kind is None:
        raise ValueError(
            f"Field {field_name!r} không thuộc domain {domain!r}. "
            f"Các field hợp lệ: {sorted(fields)}."
        )
    return kind


def is_valid_operator(operator: str) -> bool:
    """Kiểm tra `operator` có được Engine hỗ trợ hay không."""
    return operator in SUPPORTED_OPERATORS


def validate_constraint(
    domain: str,
    field_name: str,
    operator: str,
    name: str | None = None,
) -> None:
    """Kiểm tra cấu hình một HardConstraint của `domain`.

    Args:
        domain: Domain của điều kiện ("food").
        field_name: Tên field của ứng viên mà điều kiện áp dụng.
        operator: Toán tử so sánh.
        name: Tên hiển thị của điều kiện (chỉ để báo lỗi dễ hiểu).

    Raises:
        ValueError: Khi domain, field, operator hoặc tổ hợp field/operator không hợp lệ.
    """
    label = f" (điều kiện {name!r})" if name else ""
    fields = get_domain_constraint_config(domain)["fields"]
    if field_name not in fields:
        raise ValueError(
            f"HardConstraint{label} có field_name không hợp lệ: {field_name!r} "
            f"(domain {domain!r}). Các field hợp lệ: {sorted(fields)}."
        )
    if not is_valid_operator(operator):
        raise ValueError(
            f"HardConstraint{label} có operator không hợp lệ: {operator!r}. "
            f"Các operator hợp lệ: {sorted(SUPPORTED_OPERATORS)}."
        )
    kind = fields[field_name]
    allowed = OPERATORS_BY_KIND[kind]
    if operator not in allowed:
        raise ValueError(
            f"HardConstraint{label} không hợp lệ: operator {operator!r} không áp dụng "
            f"cho field {field_name!r} (kiểu {kind}). Operator hợp lệ: {sorted(allowed)}."
        )
