"""Rule-based fit score (1-5). Works offline; the Claude step can refine it."""

from __future__ import annotations

import re

from .models import Job

YEARS = re.compile(r"(\d+)\s*\+?\s*(?:-\s*\d+\s*)?years?", re.IGNORECASE)


def required_years(text: str) -> int | None:
    found = [int(m.group(1)) for m in YEARS.finditer(text) if int(m.group(1)) < 20]
    return min(found) if found else None


def rule_score(job: Job, skills: list[str]) -> tuple[int, str]:
    text = f"{job.title} {job.description}".lower()
    hits = sorted({s for s in skills if s.lower() in text})
    score = 2 + min(len(hits), 6) // 2  # 2..5 from skill overlap

    years = required_years(job.description)
    if years is not None and years >= 3:
        score -= 2
    elif years == 2:
        score -= 1
    if job.auth_flags:
        score -= 1

    score = max(1, min(5, score))
    reason = f"Matches: {', '.join(hits[:6])}." if hits else "Few direct skill matches."
    if years is not None:
        reason += f" Asks for {years}+ years."
    return score, reason
