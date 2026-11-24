"""Utility functions shared across decision engine modules."""

from typing import Any

def _get_field(candidate: Any, field_name: str, default: Any = None) -> Any:
    """Return the value of *field_name* from *candidate*.
    Supports dicts, Pydantic models, and SQLAlchemy ORM objects.
    """
    if isinstance(candidate, dict):
        return candidate.get(field_name, default)
    return getattr(candidate, field_name, default)

