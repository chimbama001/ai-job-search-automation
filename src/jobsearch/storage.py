from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from .models import STATUSES, Job

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY,
  url TEXT UNIQUE NOT NULL,
  source TEXT, company TEXT, title TEXT, location TEXT, category TEXT,
  posted TEXT, salary TEXT, fit INTEGER, why TEXT, auth_flags TEXT,
  status TEXT NOT NULL DEFAULT 'new',
  added_at TEXT NOT NULL, applied_at TEXT
);
"""


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class Store:
    def __init__(self, path: str | Path = "data/jobs.db"):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)

    def known_urls(self) -> set[str]:
        return {r[0] for r in self.db.execute("SELECT url FROM jobs")}

    def add(self, job: Job) -> bool:
        cur = self.db.execute(
            "INSERT OR IGNORE INTO jobs (id,url,source,company,title,location,category,posted,"
            "salary,fit,why,auth_flags,added_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                job.id,
                job.url,
                job.source,
                job.company,
                job.title,
                job.location,
                job.category,
                job.posted.isoformat() if job.posted else None,
                job.salary,
                job.fit,
                job.why,
                json.dumps(job.auth_flags),
                now(),
            ),
        )
        self.db.commit()
        return cur.rowcount == 1

    def all(self) -> list[dict]:
        rows = self.db.execute("SELECT * FROM jobs ORDER BY fit DESC, added_at DESC").fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["auth_flags"] = json.loads(d["auth_flags"] or "[]")
            out.append(d)
        return out

    def set_status(self, job_id: str, status: str) -> bool:
        if status not in STATUSES:
            raise ValueError(f"status must be one of {', '.join(STATUSES)}")
        applied = now() if status == "applied" else None
        cur = self.db.execute(
            "UPDATE jobs SET status=?, applied_at=COALESCE(applied_at, ?) WHERE id=?",
            (status, applied, job_id),
        )
        self.db.commit()
        return cur.rowcount == 1
