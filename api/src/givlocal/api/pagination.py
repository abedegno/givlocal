"""Pagination utilities for list endpoints."""

from __future__ import annotations

import math
from typing import Any

from givlocal.api.schemas import (
    PaginatedResponse,
    PaginationLinks,
    PaginationMeta,
)


def paginate(
    items: list[Any],
    page: int,
    per_page: int,
    base_url: str,
) -> PaginatedResponse:
    """Slice items for the requested page and build a PaginatedResponse.

    Args:
        items: Full list of items to paginate.
        page: 1-based page number requested.
        per_page: Number of items per page.
        base_url: Base URL path used to build pagination links.

    Returns:
        A PaginatedResponse with sliced data, links, and meta.
    """
    total = len(items)
    last_page = max(1, math.ceil(total / per_page)) if per_page > 0 else 1

    start = (page - 1) * per_page
    end = start + per_page
    page_items = items[start:end]

    from_index = start + 1 if page_items else 0
    to_index = start + len(page_items)

    first_url = f"{base_url}?page=1&per_page={per_page}"
    last_url = f"{base_url}?page={last_page}&per_page={per_page}"
    prev_url = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_url = f"{base_url}?page={page + 1}&per_page={per_page}" if page < last_page else None

    links = PaginationLinks(
        first=first_url,
        last=last_url,
        prev=prev_url,
        next=next_url,
    )

    meta = PaginationMeta(
        current_page=page,
        from_=from_index,
        last_page=last_page,
        path=base_url,
        per_page=per_page,
        to=to_index,
        total=total,
    )

    return PaginatedResponse(data=page_items, links=links, meta=meta)
