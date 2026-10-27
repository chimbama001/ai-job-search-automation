# Architecture

## Data flow

1. **Sources** (`sources/*.py`). Each ATS module has a pure `parse(payload, company)` function and a thin `fetch(slug)` wrapper. Keeping parsing pure means every parser is unit-tested against fixture payloads with no network access. All HTTP goes through `sources/http.py`, which sets an identifying User-Agent and waits at least one second between requests.

   | ATS | Endpoint | Date field used |
   |---|---|---|
   | Greenhouse | `boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true` | `first_published`, else `updated_at` |
   | Lever | `api.lever.co/v0/postings/{slug}?mode=json` | `createdAt` (epoch ms) |
   | Ashby | `api.ashbyhq.com/posting-api/job-board/{slug}` | `publishedAt` |

2. **Screening** (`screening.py`). Deterministic and fully tested:
   - `classify(title)` maps a title to one of four tracks, checked in a fixed order so "Security Sales Development Rep" lands in SDR/BDR.
   - `is_entry_level(title)` rejects senior, lead, manager, director, architect and level II/III titles.
   - `is_fresh(posted, today, max_age_days)` keeps postings from the last 21 days. Missing or future dates fail closed.
   - `auth_flags(text)` returns which of `citizenship`, `clearance`, `no_sponsorship` and `itar` appear. An equal-opportunity line that merely mentions "citizenship status" does not trigger a flag.

3. **Scoring** (`scoring.py`). Start at 2, add up to 3 for overlap with the profile's skills, subtract for required experience (2 years: −1, 3+ years: −2) and for authorization flags, then clamp to 1–5. It is cheap, explainable and works offline.

4. **Ranking and cap** (`pipeline.py`). Sort by preferred location, then score, then recency, and keep `daily_cap` jobs. Only those go to the LLM, which bounds API cost per run.

5. **LLM enrichment** (`llm.py`, optional). One short request per job. The output is validated by `validate()` and discarded if it is malformed.

6. **Storage** (`storage.py`). One SQLite table. `url` is unique, so re-runs never duplicate a job. `applied_at` is stamped the first time a job moves to *applied*.

7. **Dashboard** (`server.py` + `dashboard/index.html`). A stdlib `ThreadingHTTPServer` on `127.0.0.1` exposes `GET /api/jobs` and `PATCH /api/jobs/{id}`. The single-file UI polls every 60 seconds.

## Prototype history

The first version ran as an agentic workflow: a scheduled AI agent searched job boards each weekday morning, screened postings and wrote them into a hosted tracker, while the candidate approved jobs and submitted applications by hand. This repository turns that workflow into deterministic, testable code. The LLM is now limited to the one step where judgement helps (fit scoring), and everything else is plain rules.
