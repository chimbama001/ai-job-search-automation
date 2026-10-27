"""Deterministic filters: role category, seniority, freshness, location, auth language."""

from __future__ import annotations

import re
from datetime import date

# Order matters: the first category whose pattern matches the title wins.
CATEGORY_PATTERNS: list[tuple[str, re.Pattern]] = [
    (
        "SDR/BDR",
        re.compile(
            r"\b(sales|business|account) development rep|\b[sb]dr\b|\badr\b|"
            r"\bsales development\b|\bbusiness development representative\b",
            re.IGNORECASE,
        ),
    ),
    (
        "Security Analyst",
        re.compile(
            r"\b(security|soc|cyber ?security|grc|vulnerability|threat|information security)\b.*"
            r"\b(analyst|associate|specialist)\b|\bsoc analyst\b",
            re.IGNORECASE,
        ),
    ),
    (
        "Sys Admin",
        re.compile(
            r"\b(system|systems|sys|it|windows|linux|m365|microsoft 365) ?admin(istrator)?\b",
            re.IGNORECASE,
        ),
    ),
    (
        "IT Help Desk",
        re.compile(
            r"\bhelp ?desk\b|\bservice desk\b|\bdesktop support\b|\bit support\b|"
            r"\btechnical support\b|\bsupport (analyst|specialist|technician|engineer)\b|"
            r"\bit (technician|specialist)\b|\bfield tech",
            re.IGNORECASE,
        ),
    ),
]

SENIOR = re.compile(
    r"\b(senior|sr\.?|staff|principal|lead|manager|director|head of|vp|architect|ii{1,2}\b|iii\b)",
    re.IGNORECASE,
)

# Phrases that signal citizenship, clearance or sponsorship limits.
AUTH_PATTERNS: dict[str, re.Pattern] = {
    "citizenship": re.compile(
        r"\bu\.?s\.? citizen(ship)?\b|\bcitizenship (is )?required\b", re.IGNORECASE
    ),
    "clearance": re.compile(
        r"\b(active|current|ability to obtain|eligible (for|to obtain))\b[^.]{0,40}\bclearance\b|"
        r"\b(secret|top secret|ts/sci|public trust)\b[^.]{0,20}\bclearance\b",
        re.IGNORECASE,
    ),
    "no_sponsorship": re.compile(
        r"\b(not|unable to|cannot|won't|will not|do not|does not)\b[^.]{0,30}\bsponsor|"
        r"\bwithout (the need for )?(visa )?sponsorship\b|\bno (visa )?sponsorship\b",
        re.IGNORECASE,
    ),
    "itar": re.compile(r"\bitar\b|\bexport control", re.IGNORECASE),
}


def classify(title: str) -> str | None:
    for category, pattern in CATEGORY_PATTERNS:
        if pattern.search(title):
            return category
    return None


def is_entry_level(title: str) -> bool:
    return not SENIOR.search(title)


def is_fresh(posted: date | None, today: date, max_age_days: int) -> bool:
    """Unknown dates fail closed: a job we can't date is treated as stale."""
    return posted is not None and 0 <= (today - posted).days <= max_age_days


def location_rank(location: str, targets: list[str]) -> int:
    """0 = matches a preferred location, 1 = elsewhere."""
    loc = location.lower()
    return 0 if any(t.lower() in loc for t in targets) else 1


def auth_flags(text: str) -> list[str]:
    return [name for name, pattern in AUTH_PATTERNS.items() if pattern.search(text)]
