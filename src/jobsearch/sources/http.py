from __future__ import annotations

import json
import time
import urllib.request

USER_AGENT = "ai-job-search-automation/0.1 (personal job search; low volume)"
_last_call = 0.0


def get_json(url: str, timeout: float = 20.0, min_interval: float = 1.0):
    """GET a JSON document with a polite delay between requests."""
    global _last_call
    wait = min_interval - (time.monotonic() - _last_call)
    if wait > 0:
        time.sleep(wait)
    req = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.load(resp)
    finally:
        _last_call = time.monotonic()
