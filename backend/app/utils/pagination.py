"""Pagination helpers."""

from __future__ import annotations

from typing import Tuple


def normalize_pagination(limit: int | None, offset: int | None, *, max_limit: int = 200) -> Tuple[int, int]:
    limit = limit or max_limit
    limit = min(max(limit, 1), max_limit)
    offset = max(offset or 0, 0)
    return limit, offset
