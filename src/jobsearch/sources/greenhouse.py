from __future__ import annotations

from urllib.parse import quote

from ..models import Job
from ..text import html_to_text, parse_date
from .http import get_json

URL = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"


def parse(payload: dict, company: str) -> list[Job]:
    jobs = []
    for item in payload.get("jobs", []):
        jobs.append(
            Job(
                source="greenhouse",
                company=company,
                title=item.get("title", "").strip(),
                location=(item.get("location") or {}).get("name", ""),
                url=item.get("absolute_url", ""),
                posted=parse_date(item.get("first_published") or item.get("updated_at")),
                description=html_to_text(item.get("content")),
            )
        )
    return jobs


def fetch(slug: str) -> list[Job]:
    return parse(get_json(URL.format(slug=quote(slug))), company=slug.title())
