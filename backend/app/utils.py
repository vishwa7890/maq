"""Utility helpers for QuoteMaster backend."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, List


ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def now_iso() -> str:
    """Return current UTC timestamp in ISO format."""
    return datetime.now(tz=timezone.utc).strftime(ISO_FORMAT)


def dedupe_preserve_order(items: Iterable[str]) -> List[str]:
    """Remove duplicates while preserving order."""
    seen = set()
    out: List[str] = []
    for it in items:
        if it not in seen:
            seen.add(it)
            out.append(it)
    return out
