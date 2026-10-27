from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .models import STATUSES
from .pipeline import Config, run
from .server import serve
from .storage import Store


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="jobsearch", description="Human-in-the-loop job search.")
    ap.add_argument("--config", default="config.toml")
    ap.add_argument("--db", default="data/jobs.db")
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="fetch, screen, score and store new postings")
    r.add_argument("--no-llm", action="store_true", help="skip Claude enrichment")
    sub.add_parser("list", help="print tracked jobs")
    s = sub.add_parser("status", help="update a job's status")
    s.add_argument("job_id")
    s.add_argument("status", choices=STATUSES)
    sub.add_parser("demo", help="load fictional sample jobs into data/demo.db and serve them")
    v = sub.add_parser("serve", help="open the local dashboard")
    v.add_argument("--port", type=int, default=8765)

    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if args.cmd == "demo":
        from .demo import seed

        store = Store("data/demo.db")
        path = args.config if Path(args.config).exists() else "config.example.toml"
        cfg = Config.load(path) if Path(path).exists() else Config()
        rep = seed(store, cfg)
        print(f"Demo: {len(rep.added)} sample jobs kept, dropped {rep.dropped}.")
        serve(store)
        return 0
    store = Store(args.db)

    if args.cmd == "run":
        rep = run(Config.load(args.config), store, use_llm=not args.no_llm)
        print(f"Fetched {rep.fetched} postings, added {len(rep.added)}.")
        for job in sorted(rep.added, key=lambda j: -j.fit)[:5]:
            flag = f"  [{', '.join(job.auth_flags)}]" if job.auth_flags else ""
            print(f"  {job.fit}/5  {job.company}: {job.title} ({job.location}){flag}")
        for reason, n in sorted(rep.dropped.items(), key=lambda x: -x[1]):
            print(f"  dropped {n}: {reason}")
        for err in rep.errors:
            print(f"  error: {err}", file=sys.stderr)
    elif args.cmd == "list":
        for j in store.all():
            print(f"{j['status']:<10} {j['fit']}/5  {j['company']}: {j['title']}  {j['id']}")
    elif args.cmd == "status":
        if not store.set_status(args.job_id, args.status):
            print("No job with that id.", file=sys.stderr)
            return 1
    elif args.cmd == "serve":
        serve(store, args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
