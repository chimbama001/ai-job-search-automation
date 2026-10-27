from __future__ import annotations

import html
import re
from datetime import UTC, date, datetime

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def html_to_text(raw: str | None) -> str:
    """Strip tags from (possibly double-escaped) HTML and collapse whitespace."""
    if not raw:
        return ""
    text = html.unescape(html.unescape(raw))
    text = _TAG.sub(" ", text)
    return _WS.sub(" ", text).strip()


def parse_date(value: str | float | None) -> date | None:
    """Accept ISO-8601 strings or epoch milliseconds; return a UTC calendar date."""
    if value in (None, ""):
        return None
    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value / 1000, tz=UTC).date()
        return datetime.fromisoformat(str(value)).astimezone(UTC).date()
    except (ValueError, OSError, OverflowError):
        return None
