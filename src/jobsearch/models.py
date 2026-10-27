from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import date

STATUSES = ("new", "apply", "applied", "interview", "offer", "rejected", "skip")
CATEGORIES = ("IT Help Desk", "Sys Admin", "Security Analyst", "SDR/BDR")


@dataclass
class Job:
    source: str
    company: str
    title: str
    location: str
    url: str
    posted: date | None
    description: str = ""
    salary: str | None = None
    # Filled in by screening and scoring.
    category: str | None = None
    auth_flags: list[str] = field(default_factory=list)
    fit: int = 0
    why: str = ""

    @property
    def id(self) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", f"{self.company}-{self.title}".lower()).strip("-")[:60]
        digest = hashlib.sha1(self.url.encode()).hexdigest()[:8]
        return f"{slug}-{digest}"
