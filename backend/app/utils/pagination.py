"""Pure pagination math, extracted so it can be unit tested and reused outside
the Page[T] schema (e.g. for building "X of Y pages" copy in explanations/UIs)."""

from __future__ import annotations


def compute_total_pages(total: int, page_size: int) -> int:
    """Number of pages needed to cover `total` items at `page_size` per page.

    Returns 0 if page_size is 0 (avoids a ZeroDivisionError on malformed input;
    callers validate page_size > 0 via Pydantic before this is ever reached)."""
    if page_size <= 0:
        return 0
    return (total + page_size - 1) // page_size


def clamp_page(page: int, total_pages: int) -> int:
    """Clamps a requested page number into the valid [1, total_pages] range,
    treating an empty result set (total_pages == 0) as page 1."""
    if total_pages <= 0:
        return 1
    return max(1, min(page, total_pages))
