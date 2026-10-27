"""Public applicant-tracking-system job board APIs.

Each module exposes `parse(payload, company)` (pure, unit-tested) and
`fetch(slug)` (network). Only documented public JSON endpoints are used,
so no scraping, logins or CAPTCHAs are involved.
"""

from . import ashby, greenhouse, lever

REGISTRY = {"greenhouse": greenhouse, "lever": lever, "ashby": ashby}
