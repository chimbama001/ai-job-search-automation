"""Offline demo: fictional postings run through the real screen + score steps."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .models import Job
from .pipeline import Config, Report, screen
from .scoring import rule_score
from .storage import Store

# Fictional companies and postings, for trying the dashboard without network access.
SAMPLES = [
    (
        "Northwind Security",
        "Sales Development Representative",
        "Boston, MA (Hybrid)",
        2,
        (
            "Outbound cold calling and email to security leaders. Salesforce and Sales Navigator. "
            "1+ years in SaaS sales development."
        ),
        "$70K-$85K OTE",
    ),
    (
        "Harbor Cloud",
        "Business Development Representative",
        "Remote (US)",
        5,
        "Prospect mid-market IT teams, book meetings for AEs, keep CRM clean in HubSpot.",
        None,
    ),
    (
        "Lumen Health IT",
        "IT Help Desk Technician",
        "Atlanta, GA",
        1,
        "Tier 1 support, Active Directory resets, Microsoft 365, ticketing in ServiceNow.",
        "$22-$26/hr",
    ),
    (
        "Bayline Federal",
        "SOC Analyst I",
        "Austin, TX",
        3,
        (
            "Monitor SIEM alerts and triage incidents. Must be a U.S. citizen with ability to obtain "
            "a Secret clearance."
        ),
        None,
    ),
    (
        "Cedar Systems",
        "Junior Systems Administrator",
        "New York, NY",
        8,
        "Windows and Linux servers, Azure, patching, backups. 0-2 years experience.",
        "$65K-$75K",
    ),
    (
        "Keystone Retail",
        "Security Analyst",
        "Tampa, FL",
        12,
        "Vulnerability management, NIST frameworks, security awareness training.",
        None,
    ),
    ("Old Mill Software", "SDR", "Boston, MA", 40, "Posting from last month.", None),
    ("Summit Data", "Senior Security Engineer", "Remote (US)", 1, "8+ years.", None),
]


def seed(store: Store, cfg: Config) -> Report:
    today = datetime.now(timezone.utc).date()
    jobs = [
        Job(
            source="demo",
            company=c,
            title=t,
            location=loc,
            posted=today - timedelta(days=age),
            url=f"https://example.com/jobs/{c.lower().replace(' ', '-')}",
            description=d,
            salary=s,
        )
        for c, t, loc, age, d, s in SAMPLES
    ]
    report = Report(fetched=len(jobs))
    for job in screen(jobs, cfg, store.known_urls(), today, report):
        job.fit, job.why = rule_score(job, cfg.skills)
        job.why = "[Demo data] " + job.why
        if store.add(job):
            report.added.append(job)
    return report
