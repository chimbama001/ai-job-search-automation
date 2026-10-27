from datetime import date

from jobsearch.sources import ashby, greenhouse, lever

GREENHOUSE = {
    "jobs": [
        {
            "id": 1,
            "title": " Sales Development Representative ",
            "location": {"name": "Boston, MA"},
            "absolute_url": "https://boards.greenhouse.io/acme/jobs/1",
            "first_published": "2026-10-20T14:00:00-04:00",
            "updated_at": "2026-10-25T10:00:00-04:00",
            "content": "&lt;p&gt;Use &lt;b&gt;Salesforce&lt;/b&gt; daily.&lt;/p&gt;",
        }
    ]
}

LEVER = [
    {
        "text": "IT Support Specialist",
        "categories": {"location": "Austin, TX"},
        "workplaceType": "remote",
        "hostedUrl": "https://jobs.lever.co/acme/abc",
        "createdAt": 1761350400000,  # 2025-10-25T00:00:00Z
        "descriptionPlain": "Support users.",
        "lists": [{"text": "Requirements", "content": "1+ years help desk"}],
    }
]

ASHBY = {
    "jobs": [
        {
            "title": "SOC Analyst",
            "location": "New York",
            "isRemote": False,
            "isListed": True,
            "jobUrl": "https://jobs.ashbyhq.com/acme/1",
            "publishedAt": "2026-10-26T09:00:00.000+00:00",
            "descriptionPlain": "Monitor the SIEM.",
            "compensation": {"compensationTierSummary": "$70K - $85K"},
        },
        {"title": "Hidden", "isListed": False, "jobUrl": "x"},
    ]
}


def test_greenhouse_parse():
    [job] = greenhouse.parse(GREENHOUSE, "Acme")
    assert job.title == "Sales Development Representative"
    assert job.posted == date(2026, 10, 20)  # first_published wins over updated_at
    assert job.description == "Use Salesforce daily."


def test_lever_parse():
    [job] = lever.parse(LEVER, "Acme")
    assert job.location == "Austin, TX (Remote)"
    assert job.posted == date(2025, 10, 25)
    assert "1+ years help desk" in job.description


def test_ashby_parse_skips_unlisted():
    jobs = ashby.parse(ASHBY, "Acme")
    assert [j.title for j in jobs] == ["SOC Analyst"]
    assert jobs[0].salary == "$70K - $85K"
