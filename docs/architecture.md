# Yanki — Architecture

*Audience: engineers / on-call. This document describes **what session 1 actually
builds** — system + data-flow diagrams, the job lifecycle, and the deploy
topology. For the **why** behind these choices (the ADR log), see
[design.md](design.md). For **scope** see [02-mvp.md](02-mvp.md); for **how
"done" is verified** see [test-suite.md](test-suite.md).*

---

## 1. System at a glance

Four processes, one Postgres. The api and the worker are the **same Docker
image** (built from `backend/Dockerfile`) started with different commands — the
api serves HTTP, the worker polls the queue. There is no message broker: the
`analyses` table *is* the queue (see §4).

```
                        ┌─────────────────────────────────────────┐
                        │                Browser                   │
                        └───────────────────┬─────────────────────┘
                                            │  HTTP (same origin)
                                            ▼
                        ┌─────────────────────────────────────────┐
   web (Next.js 15) ───▶│  web  :8140   App Router, 3 screens      │
                        │               fetch()s relative /api/... │
                        └───────────────────┬─────────────────────┘
             dev: Next.js rewrites() proxy  │  prod: shared Caddy path-routes
             /api/:path* + /healthz → 8141   │  /api/* + /healthz → 8141
                                            ▼
                        ┌─────────────────────────────────────────┐
   api (FastAPI, sync) │  api  :8141   POST /api/v1/analyses (202) │
                        │               GET  /api/v1/analyses/{id} │
                        │               GET  /healthz              │
                        └───────────────────┬─────────────────────┘
                                            │  INSERT row status='queued'
                                            ▼
                        ┌─────────────────────────────────────────┐
                        │           Postgres 16  (db)              │
                        │  analyses │ prompts │ responses │        │
                        │           │         │ llm_cache          │
                        │  analyses table doubles as the job queue │
                        └───────────────────┬─────────────────────┘
                                            ▲
                                            │  claim (FOR UPDATE SKIP LOCKED),
                                            │  run 6 steps, persist, heartbeat
                        ┌───────────────────┴─────────────────────┐
   worker (sync loop)  │  worker       while True: poll + sleep    │
                        │               runs backend/app/pipeline/ │
                        │               calls providers/ (LLM)     │
                        └───────────────────┬─────────────────────┘
                                            │  DRY_RUN=1 → mock; else real/stub
                                            ▼
                        ┌─────────────────────────────────────────┐
                        │  LLM providers: anthropic (real),        │
                        │  openai (real), gemini + perplexity      │
                        │  (stub), mock (deterministic, $0)        │
                        └─────────────────────────────────────────┘
```

Components (all in this repo):

| Component | Where | Port | Role |
|---|---|---|---|
| web | `frontend/` | 8140 | Next.js 15 App Router UI; submit + poll + render. |
| api | `backend/` (`app.api.main:app`) | 8141 | FastAPI, **sync**; validates + enqueues + serves status/results. |
| worker | `backend/` (`app.worker`) | — | Same image as api; polls the queue, runs the pipeline. |
| db | Postgres 16 | 5432 (dev only) | System of record **and** the job queue. |

The api never calls an LLM and never runs a pipeline step; it only reads/writes
rows. All the slow, costly work happens in the worker.

---

## 2. Data flow — the 6-step pipeline

One analysis walks six steps in order. Each step is a plain sync function under
`backend/app/pipeline/`; the worker runs them sequentially in one job, persisting
after each step so a crash never loses completed work and partial results stay
queryable (FR-7).

```
 URL
  │
  ▼
┌───────────────┐  discovery.discover(url) -> str
│ 1. discovery  │  httpx GET (15s, UA "YankiBot/0.1"), BeautifulSoup strip
│               │  script/style/nav; homepage + ≤5 same-domain links; ~20k cap
│               │  unreachable/empty -> PipelineError("could not read the site")
└──────┬────────┘  ── on complete: progress = 15, current_step advances
       ▼
┌───────────────┐  kyc.generate_kyc(text, url, provider) -> KYC
│ 2. kyc        │  ONE LLM call, strict JSON (strip ```json fences), Pydantic
│               │  KYC model. aliases always include company name + domain-sans-TLD
│               │  persisted to analyses.kyc (jsonb)
└──────┬────────┘  ── progress = 30
       ▼
┌───────────────┐  prompts.generate_prompts(kyc, count) -> list[PromptSpec]
│ 3. prompts    │  DETERMINISTIC templates, NO LLM. cycles categories
│               │  recommendation/comparison/alternatives/best-of/use-case
│               │  exactly PROMPT_COUNT, non-empty, no duplicates -> prompts rows
└──────┬────────┘  ── progress = 45
       ▼
┌───────────────┐  execute: for each prompt × each panel engine
│ 4. execute    │  consult llm_cache (fresh <24h) else provider.generate()
│               │  insert responses row + llm_cache row; persist per response
│               │  stop at MAX_RESPONSES_PER_JOB (log, don't error)
└──────┬────────┘  ── progress = 80
       ▼
┌───────────────┐  footprint.detect(raw_text, kyc) -> (bool, snippet|None)
│ 5. footprint  │  PURE, deterministic, case-insensitive search of
│               │  company/aliases/domain; ±60-char snippet on first hit
│               │  updates each responses.footprint + matched_snippet
└──────┬────────┘  ── progress = 90
       ▼
┌───────────────┐  scoring.geo_score(footprints, total) -> float
│ 6. scoring    │  PURE; footprint_count / total_responses; 0.0 when total==0
│               │  writes analyses.geo_score, footprint_count, total_responses
└──────┬────────┘  ── progress = 100, status = 'done'
       ▼
 RESULTS (GET /api/v1/analyses/{id} → result{ kyc, prompts, responses, geo_score })
```

### Progress mapping (SPEC — set when the step COMPLETES)

| After step | `current_step` during | `progress` on complete | `status` |
|---|---|---|---|
| (enqueued) | `null` | 0 | queued |
| 1 discovery | `discovery` | 15 | running |
| 2 kyc | `kyc` | 30 | running |
| 3 prompts | `prompts` | 45 | running |
| 4 execute | `execute` | 80 | running |
| 5 footprint | `footprint` | 90 | running |
| 6 scoring | `scoring` | 100 | done |

`current_step ∈ discovery|kyc|prompts|execute|footprint|scoring|null`. The
frontend polls `GET` every 2s and renders the 6-step `StepProgress` from
`current_step` + `progress` until `status` is `done` (→ `ScoreGauge` +
`ResultsTable`) or `failed` (→ danger card with `error` + retry link).

### DRY_RUN / mock provider path

`DRY_RUN` defaults to **true** (safe by default). It changes exactly one thing:
which providers the worker uses. `providers/registry.py`:

- `get_panel(settings)` → **DRY_RUN=1**: four `MockProvider`s named after the
  panel engines. **DRY_RUN=0**: maps `PANEL_ENGINES` to real
  (anthropic, openai) / stub (gemini, perplexity) providers.
- `get_analysis_provider(settings)` → the single provider used for the KYC call
  (mock when DRY_RUN).

`MockProvider` is deterministic: it mentions the company name iff
`sha256(prompt).digest()[0] % 2 == 0`, adds filler brands, and costs **$0**. So
the entire 6-step flow — and the whole test suite — runs offline at zero spend
and produces a stable, non-trivial score. Stub engines (gemini/perplexity) also
cost $0 and return a canned answer that *sometimes mentions nothing*, so
footprint detection sees both outcomes even outside DRY_RUN.

### llm_cache behavior

`execute` consults `llm_cache` before every provider call. Key =
`sha256("engine:model:prompt_text")`. A row **fresh within 24h** is reused (no
provider call, cost counted from the cached row); a **stale** row is ignored and
overwritten. This is a **within-job / cross-job cost guard**, not a cross-account
product cache (that's out of scope — see 02-mvp.md §4). TTL is enforced at read
time, not by a sweeper.

---

## 3. Request lifecycles (submit vs. poll)

```
Submit:
  Browser ── POST /api/v1/analyses {url} ──▶ api
                                            api validates URL (http/https only)
                                            invalid → 422 (Pydantic shape)
                                            valid   → INSERT analyses (status=queued)
  Browser ◀─────────── 202 {id} ───────────  (returns immediately; no work yet)

Poll (every 2s):
  Browser ── GET /api/v1/analyses/{id} ────▶ api
                                            api reads analyses + prompts + responses
  Browser ◀── 200 {status, progress,        result{} is ALWAYS present;
              current_step, result{…}} ──    inner fields null/empty until produced
                                            unknown id → 404
```

`result` is always present so the frontend renders partial state as the pipeline
fills it in. See the locked response shape in SPEC §"API contract".

---

## 4. Job lifecycle — Postgres as the queue

The queue is the `analyses` table; there is no broker (NFR-4). The worker
(`backend/app/worker.py`) is a `while True` loop that sleeps `WORKER_POLL_SECONDS`
(default 2) between polls.

```
                 POST creates row
                        │
                        ▼
                  ┌───────────┐
                  │  queued   │  attempts=0, claimed_at=null, progress=0
                  └─────┬─────┘
        worker claim TX │  (one transaction, one row)
                        ▼
                  ┌───────────┐   heartbeat: worker bumps claimed_at
                  │  running  │◀─ between steps so a live job is not
                  └──┬─────┬──┘   mistaken for stale
        pipeline ok  │     │  any exception in a step
                     ▼     ▼
              ┌────────┐  ┌────────┐
              │  done  │  │ failed │  error=str(exc)[:500], partial rows kept
              └────────┘  └────────┘
                     ▲
   stale reclaim ────┘   a 'running' row whose claimed_at is older than
                         STALE_CLAIM_SECONDS is re-claimable (crashed worker).
                         attempts>3 on reclaim → failed, error='max retries exceeded'
```

### The claim query (the whole concurrency story)

One transaction selects **one** job and marks it running:

```sql
SELECT id FROM analyses
WHERE status = 'queued'
   OR (status = 'running' AND claimed_at < now() - :stale_interval)
ORDER BY created_at
LIMIT 1
FOR UPDATE SKIP LOCKED;   -- concurrent workers never grab the same row
-- then: UPDATE ... SET status='running', claimed_at=now(), attempts=attempts+1
```

- **`FOR UPDATE SKIP LOCKED`** — two workers polling at once each get a
  *different* row (or none); a job is never double-run (NFR-3). This is the only
  coordination primitive; it needs no broker and no advisory locks.
- **Stale-claim reaper via `claimed_at`** — the same `WHERE` also matches a
  `running` row whose `claimed_at` has aged past `STALE_CLAIM_SECONDS` (default
  300). A worker that crashes mid-job leaves such a row; the next poll reclaims
  it. The heartbeat (worker bumps `claimed_at` between steps) keeps a genuinely
  live long job from being reaped.
- **`attempts > 3` → failed** — each claim increments `attempts`. On the reclaim
  path, a job that has already been attempted more than 3 times is set to
  `failed` with `error='max retries exceeded'` instead of running again, so a
  poison job can't loop forever.
- **Failure containment** — any exception raised inside the pipeline sets
  `status='failed'`, `error=str(exc)` truncated to 500 chars, and leaves the rows
  written so far in place (FR-7 partial results).

State-transition summary:

| From | Trigger | To |
|---|---|---|
| queued | worker claims it | running |
| running | all 6 steps succeed | done |
| running | exception in a step | failed |
| running (claimed_at stale) | reclaimed, attempts ≤ 3 | running |
| running (claimed_at stale) | reclaimed, attempts > 3 | failed (max retries) |

---

## 5. Deploy topology

### Dev (`make dev`)

`docker compose -f deploy/docker-compose.yml up --build` brings up **db + api +
worker + web** with bind-mounts for hot reload. **No CORS**: the frontend always
fetches relative paths, and Next.js `rewrites()` proxies `/api/:path*` and
`/healthz` to the api (`API_ORIGIN`, default `http://localhost:8141`). Postgres
publishes 5432 for local psql only.

```
 laptop
   http://localhost:8140  ──▶  web (Next.js dev)
                                 └─ rewrites /api/* + /healthz ─▶ api :8141
   http://localhost:8141/healthz ─────────────────────────────▶ api :8141
                                     api ─┐   worker ─┐
                                          └── db :5432 ┘  (same compose network)
```

### Prod (shared pulse-prod Caddy on `test.beyondkaira.com`)

Yanki runs **no Caddy of its own**. The shared **pulse-prod Caddy** terminates
TLS on `test.beyondkaira.com` and **path-routes** on one origin (so still no
CORS):

```
 Internet ──TLS──▶ test.beyondkaira.com  (shared pulse-prod Caddy)
                        │
                        ├─ /api/*  + /healthz ──▶ api  :8141
                        └─ everything else ──────▶ web  :8140
                                                    api + worker + db
                                                    (compose project yanki-prod)
```

- Compose project name is **`yanki-prod`**. Yanki publishes only 8140/8141,
  bound so **only the shared Caddy** can reach them; Postgres is never published
  in prod (internal network only).
- `make deploy` / `make rollback` follow the ams-pulse pattern: build, tag by git
  SHA, `compose -p yanki-prod up`, `/healthz` check, roll back to the last-good
  SHA file on failure. **Marked UNTESTED tech debt.**

**One-time prerequisites** (done once by an admin — from README §Deploy):

1. On the server, `cp deploy/.env.example deploy/.env` and fill in real secrets.
   `make deploy` refuses to run without it and never auto-creates secrets.
2. Point DNS: A record `test.beyondkaira.com → 161.97.172.146`.
3. Drop `deploy/caddy/test.beyondkaira.com.caddy` into the shared pulse-prod
   Caddy import dir, then `caddy validate` and **reload** (never restart) that
   Caddy.

---

## 6. On-call quick reference

| Symptom | Where to look |
|---|---|
| Job stuck in `queued` | Is the **worker** process up? It's the same image as api, separate command. Check `make deploy-logs`. |
| Job stuck in `running` forever | Worker crashed mid-step. It self-heals: the stale-claim reaper reclaims after `STALE_CLAIM_SECONDS` (300s). |
| Job `failed` with an error | `analyses.error` holds `str(exc)` (≤500 chars). Discovery failures read "could not read the site". Partial rows remain. |
| `max retries exceeded` | Job hit `attempts > 3` — a poison job. Inspect its `url` / `error`; don't just re-queue. |
| Unexpected LLM spend | Confirm `DRY_RUN` and `PANEL_ENGINES`; check `MAX_RESPONSES_PER_JOB` and `llm_cache` hit rate. CI/tests must stay `DRY_RUN`. |
| 404 on a valid-looking id | Unknown/never-created id. 422 instead means URL validation rejected the submit. |
| Frontend can't reach api | Dev: `rewrites()` / `API_ORIGIN`. Prod: shared Caddy path-routing + the 8140/8141 bind. |

---

*Related: [design.md](design.md) (folder rationale + ADR log — the "why"),
[02-mvp.md](02-mvp.md) (scope + acceptance criteria),
[test-suite.md](test-suite.md) (how each step is tested).*
