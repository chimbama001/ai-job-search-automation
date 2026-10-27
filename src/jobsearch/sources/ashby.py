from __future__ import annotations

from urllib.parse import quote

from ..models import Job
from ..text import html_to_text, parse_date
from .http import get_json

URL = "https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true"


def parse(payload: dict, company: str) -> list[Job]:
    jobs = []
    for item in payload.get("jobs", []):
        if item.get("isListed") is False:
            continue
        location = item.get("location", "")
        if item.get("isRemote") and "remote" not in location.lower():
            location = f"{location} (Remote)".strip()
        comp = (item.get("compensation") or {}).get("compensationTierSummary")
        jobs.append(
            Job(
                source="ashby",
                company=company,
                title=item.get("title", "").strip(),
                location=location,
                url=item.get("jobUrl", ""),
                posted=parse_date(item.get("publishedAt")),
                description=item.get("descriptionPlain")
                or html_to_text(item.get("descriptionHtml")),
                salary=comp or None,
            )
        )
    return jobs


def fetch(slug: str) -> list[Job]:
    return parse(get_json(URL.format(slug=quote(slug))), company=slug.title())
