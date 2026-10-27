from datetime import date

import pytest

from jobsearch import screening


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("Sales Development Representative", "SDR/BDR"),
        ("Business Development Representative, Growth", "SDR/BDR"),
        ("BDR - Enterprise", "SDR/BDR"),
        ("SOC Analyst I", "Security Analyst"),
        ("Junior Cybersecurity Analyst", "Security Analyst"),
        ("GRC Analyst", "Security Analyst"),
        ("Systems Administrator", "Sys Admin"),
        ("IT Help Desk Technician", "IT Help Desk"),
        ("Technical Support Engineer", "IT Help Desk"),
        ("Software Engineer", None),
        ("Account Executive", None),
    ],
)
def test_classify(title, expected):
    assert screening.classify(title) == expected


@pytest.mark.parametrize(
    ("title", "entry"),
    [
        ("Sales Development Representative", True),
        ("Senior SOC Analyst", False),
        ("Sr. Systems Administrator", False),
        ("SDR Manager", False),
        ("Help Desk Technician II", False),
        ("IT Support Specialist", True),
    ],
)
def test_entry_level(title, entry):
    assert screening.is_entry_level(title) is entry


def test_freshness_window():
    today = date(2026, 10, 27)
    assert screening.is_fresh(date(2026, 10, 6), today, 21)
    assert not screening.is_fresh(date(2026, 10, 5), today, 21)
    assert not screening.is_fresh(None, today, 21)  # undated fails closed
    assert not screening.is_fresh(date(2026, 11, 1), today, 21)  # future date is suspect


@pytest.mark.parametrize(
    ("text", "flags"),
    [
        ("Must be a U.S. citizen.", ["citizenship"]),
        ("Ability to obtain a Secret clearance is required.", ["clearance"]),
        ("Active TS/SCI clearance.", ["clearance"]),
        ("We do not currently sponsor immigration visas.", ["no_sponsorship"]),
        ("Must be authorized to work without sponsorship.", ["no_sponsorship"]),
        ("This role is subject to ITAR.", ["itar"]),
        ("Great benefits and a 401(k) match.", []),
        ("We are an equal opportunity employer regardless of citizenship status.", []),
    ],
)
def test_auth_flags(text, flags):
    assert screening.auth_flags(text) == flags


def test_location_rank():
    targets = ["Boston", "Remote"]
    assert screening.location_rank("Boston, MA", targets) == 0
    assert screening.location_rank("United States (Remote)", targets) == 0
    assert screening.location_rank("Denver, CO", targets) == 1
