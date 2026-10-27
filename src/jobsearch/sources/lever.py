from __future__ import annotations

from urllib.parse import quote

from ..models import Job
from ..text import parse_date
from .http import get_json

URL = "https://api.lever.co/v0/postings/{slug}?mode=json"


def parse(payload: list, company: str) -> list[Job]:
    jobs = []
    for item in payload or []:
        cats = item.get("categories") or {}
        location = cats.get("location", "")
        if item.get("workplaceType") == "remote" and "remote" not in location.lower():
            location = f"{location} (Remote)".strip()
        parts = [item.get("descriptionPlain", "")]
        for block in item.get("lists") or []:
            parts.append(block.get("text", ""))
            parts.append(block.get("content", ""))
        parts.append(item.get("additionalPlain", ""))
        jobs.append(
            Job(
                source="lever",
                company=company,
                title=item.get("text", "").strip(),
                location=location,
                url=item.get("hostedUrl", ""),
                posted=parse_date(item.get("createdAt")),
                description=" ".join(p for p in parts if p),
            )
        )
    return jobs


def fetch(slug: str) -> list[Job]:
    return parse(get_json(URL.format(slug=quote(slug))), company=slug.title())
