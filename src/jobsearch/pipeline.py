"""Fetch -> screen -> score -> store, capped at the daily limit."""

from __future__ import annotations

import logging
import tomllib
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path

from . import llm, screening
from .models import Job
from .scoring import rule_score
from .sources import REGISTRY
from .storage import Store

log = logging.getLogger("jobsearch")


@dataclass
class Config:
    max_age_days: int = 21
    daily_cap: int = 15
    locations: list[str] = field(default_factory=list)
    allow_anywhere: bool = True
    keep_auth_flagged: bool = True
    profile: str = ""
    skills: list[str] = field(default_factory=list)
    sources: dict[str, list[str]] = field(default_factory=dict)

    @classmethod
    def load(cls, path: str | Path) -> Config:
        raw = tomllib.loads(Path(path).read_text())
        s, p = raw.get("search", {}), raw.get("profile", {})
        return cls(
            max_age_days=s.get("max_age_days", 21),
            daily_cap=s.get("daily_cap", 15),
            locations=s.get("locations", []),
            allow_anywhere=s.get("allow_anywhere", True),
            keep_auth_flagged=s.get("keep_auth_flagged", True),
            profile=p.get("summary", ""),
            skills=p.get("skills", []),
            sources=raw.get("sources", {}),
        )


@dataclass
class Report:
    fetched: int = 0
    added: list[Job] = field(default_factory=list)
    dropped: dict[str, int] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def drop(self, reason: str) -> None:
        self.dropped[reason] = self.dropped.get(reason, 0) + 1


def screen(jobs: list[Job], cfg: Config, known: set[str], today: date, report: Report) -> list[Job]:
    kept = []
    for job in jobs:
        if not job.url or job.url in known:
            report.drop("already tracked")
            continue
        job.category = screening.classify(job.title)
        if job.category is None:
            report.drop("not a target role")
            continue
        if not screening.is_entry_level(job.title):
            report.drop("too senior")
            continue
        if not screening.is_fresh(job.posted, today, cfg.max_age_days):
            report.drop(f"older than {cfg.max_age_days} days or undated")
            continue
        if not cfg.allow_anywhere and screening.location_rank(job.location, cfg.locations):
            report.drop("outside target locations")
            continue
        job.auth_flags = screening.auth_flags(job.description)
        if job.auth_flags and not cfg.keep_auth_flagged:
            report.drop("work-authorization language")
            continue
        kept.append(job)
        known.add(job.url)
    return kept


def run(cfg: Config, store: Store, today: date | None = None, use_llm: bool = True) -> Report:
    today = today or datetime.now(UTC).date()
    report = Report()
    candidates: list[Job] = []
    for ats, slugs in cfg.sources.items():
        module = REGISTRY.get(ats)
        if module is None:
            report.errors.append(f"unknown source '{ats}'")
            continue
        for slug in slugs:
            try:
                jobs = module.fetch(slug)
            except Exception as exc:  # noqa: BLE001  one bad board must not stop the run
                report.errors.append(f"{ats}/{slug}: {exc}")
                continue
            report.fetched += len(jobs)
            candidates += jobs

    kept = screen(candidates, cfg, store.known_urls(), today, report)
    for job in kept:
        job.fit, job.why = rule_score(job, cfg.skills)

    # Preferred locations first, then best rule score, then newest.
    kept.sort(
        key=lambda j: (
            screening.location_rank(j.location, cfg.locations),
            -j.fit,
            -(j.posted.toordinal() if j.posted else 0),
        )
    )
    chosen = kept[: cfg.daily_cap]

    if use_llm and llm.available():
        for job in chosen:
            try:
                result = llm.enrich(job, cfg.profile)
            except Exception as exc:  # noqa: BLE001  enrichment is best-effort
                log.warning("Claude enrichment failed for %s: %s", job.url, exc)
                continue
            if result:
                job.fit, job.why = result["fit"], result["why"]

    for job in chosen:
        if store.add(job):
            report.added.append(job)
    return report
