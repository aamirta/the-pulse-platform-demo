"""Common API helpers for pagination, serialization, and filtering."""

import math
from decimal import Decimal
from typing import Any, TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Query

from backend.schemas import PaginatedResponse

T = TypeVar("T", bound=BaseModel)


def paginate(
    query: Query[Any],
    response_model: type[T],
    page: int,
    page_size: int,
) -> PaginatedResponse[T]:
    """Paginate a SQLAlchemy query and return a Pydantic paginated response."""
    total = query.count()
    pages = max(1, math.ceil(total / page_size))
    page = min(page, pages) if total else 1
    items_query = query.offset((page - 1) * page_size).limit(page_size)
    items = [response_model.model_validate(item) for item in items_query]
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


def split_tags(value: str | None) -> list[str]:
    """Split a comma/newline separated tag string into a clean list."""
    if not value:
        return []
    return [tag.strip() for tag in value.replace("\n", ",").split(",") if tag.strip()]


def format_currency(value: Any | None, currency: str = "USD") -> str:
    """Format a numeric value as a currency string."""
    if value is None:
        return ""
    if isinstance(value, Decimal):
        value = float(value)
    return f"{currency} {value:,.0f}"


def safe_int(value: Any | None) -> int | None:
    """Safely convert a value to int."""
    if value is None:
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def or_404(instance: Any, detail: str = "Not found") -> Any:
    """Raise 404 if instance is None, else return it."""
    if instance is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
    return instance


def apply_search_filter(
    query: Query[Any],
    model: Any,
    search: str | None,
    *fields: str,
) -> Query[Any]:
    """Apply a case-insensitive OR search across the given string fields."""
    if not search:
        return query
    from sqlalchemy import or_

    term = f"%{search}%"
    return query.filter(or_(*[getattr(model, field).ilike(term) for field in fields]))
