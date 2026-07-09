# Yanki — Implementation Plan (engineering execution)

*Audience: the founder-orchestrator and the coding agents they dispatch. This is
the **how** and **when** of the build — the ticket breakdown, sequencing, file
ownership, and status. The **what/why** (product) lives in
[roadmap.md](roadmap.md); the **scope authority** is [02-mvp.md](02-mvp.md). This
file does not duplicate either — it links to them.*

Related: [architecture.md](architecture.md) (how it's built),
[design.md](design.md) (repo structure + ownership + ADR log),
[test-suite.md](test-suite.md) (how "done" is verified),
[frontend-brandkit.md](frontend-brandkit.md) (tokens + components).

---

## How to use this doc

- **Tasks are the unit of work.** Each is sized so one autonomous agent finishes
  it in a single focused session. IDs are stable (`P<phase>.<n>`); never renumber
  — mark `superseded` instead.
- **Every task carries:** Goal · Why now · Dependencies · Complexity (S/M/L) ·
  Deliverables (files) · Acceptance criteria · Status.
- **Status vocabulary:** `todo` · `in progress — session N` · `done` ·
  `blocked (<reason>)` · `superseded`.
- **Before starting a task**, read the linked contracts and confirm no other
  agent owns your files this session (see the ownership map in
  [design.md](design.md)). **Stay inside your ownership set** — touching another
  agent's files corrupts a parallel build.
- **Cross-cutting contracts are locked** (API shapes, DB fields, env vars, ports,
  dep lists). They live in the session master SPEC and are mirrored in
  [architecture.md](architecture.md). Deviate only minimally, and record the
  deviation in your session summary.
- **The project must always run.** Build and test each pipeline step behind
  `DRY_RUN=1` before wiring a real key. Nothing Phase-4+ starts until the Phase-3
  happy path renders a score.

### Current Priority

✅ **Session 1 (2026-07-09) is complete: Phase 0 → Phase 3 landed and verified in
one orchestrated pass.** The DRY_RUN stack boots and was driven end-to-end —
`POST` a URL → `202` → the six pipeline steps run → a GEO score renders
(`geo_score=0.6`, `total_responses=40` = 10 prompts × 4 mock engines); the
failure and `422` paths hold; `make lint`/`typecheck`/`test` are green (54
backend tests incl. real-Postgres `SKIP LOCKED` queue tests on `:5433`, 9
vitest). Default ports stay web `8140` / api `8141`, now overridable via
`YANKI_WEB_PORT`/`YANKI_API_PORT`/`YANKI_DB_PORT`.

➡️ **Next up: P4.1 — real-key smoke test + Week-1 invoice check.** Phase 4 is the
path from the working DRY_RUN loop to a live, cost-validated, CI-guarded deploy.
Still pending: the real-key cost run (P4.1), the server deploy (P4.2, scripts
untested), CI hardening (P4.3), Playwright-in-CI (P4.4 — the spec exists but the
automated run was skipped in this env: chromium needs a root `install-deps`).

### Agent lanes (parallelism map)

The session runs these lanes in parallel; the merge risks are the shared
contracts between them.

| Lane | Owns | Phase-1/2/3 tasks |
|---|---|---|
| **backend-spine** | `backend/` (config, db, api, jobs, services, worker, alembic, `tests/{conftest,test_api,test_queue,test_queue_postgres}.py`, `pyproject.toml`, `Dockerfile`) | P1.1–P1.6, P2.10a |
| **pipeline** | `backend/app/pipeline/**`, `backend/app/providers/**`, `backend/tests/pipeline/**` | P2.1–P2.9, P2.10b |
| **frontend** | `frontend/**` | P1.7, P3.1–P3.5 |
| **infra** | `Makefile`, `deploy/**`, `scripts/**`, `.github/**`, `.gitignore`, `CONTRIBUTING.md`, `SECURITY.md`, README link fixes | P0.2, P1.8, P4.2–P4.4 |
| **docs** | `docs/**` (one file per agent) | P0.3 |

**Shared-contract merge risks (coordinate before editing):**
- The **API envelope** (`GET /api/v1/analyses/{id}`) binds backend-spine ↔
  frontend. It is generated into `shared/contracts/openapi.json` →
  `frontend/lib/types.ts` by `make gen-types` (P3.1) — never hand-edit those; the
  frontend imports through the hand-maintained `frontend/lib/contracts.ts` seam.
- The **`KYC` / `PromptSpec` / `ProviderResult`** shapes bind pipeline ↔
  backend-spine (the worker calls the pipeline).
- **Config env vars** bind all lanes; the locked list lives in
  [architecture.md](architecture.md) and `deploy/.env.example`.
- **DB schema** is owned by backend-spine's Alembic migration; pipeline reads/
  writes those tables via the models but may not alter the migration.

---

## Phase 0 — Repository sanity

Goal: a clean, documented, ignorable-noise-free repo a new agent can navigate.

### P0.1 — Git init + baseline commit
- **Goal:** repo under version control with an initial baseline.
- **Why now:** every later task needs a repo to branch from.
- **Dependencies:** none.
- **Complexity:** S
- **Deliverables:** initialized `.git`, baseline commit of existing docs.
- **Acceptance:** `git log` shows a baseline commit; tree is clean.
- **Status:** done

### P0.2 — .gitignore + README link/consistency fixes
- **Goal:** ignore build/venv/node/env noise; fix README doc links (README points
  at `docs/mvp.md` but the file is `docs/02-mvp.md`) and confirm the Make-target
  and port tables match the SPEC.
- **Why now:** stops secrets/artifacts leaking into commits and stops the front
  door pointing at 404s.
- **Dependencies:** P0.1.
- **Complexity:** S
- **Deliverables:** `.gitignore` (Python, Node, env files, `.venv`, `__pycache__`,
  `node_modules`, `.next`, coverage, `deploy/.env`), README link fixes.
- **Acceptance:** `git status` is clean after a build; every README doc link
  resolves to an existing file; no `deploy/.env` is trackable.
- **Status:** done (session 1)

### P0.3 — Author the doc set
- **Goal:** author/refresh the docs so no doc drifts from the planned build:
  `design.md`, `architecture.md`, `roadmap.md`, `test-suite.md`, this
  `implementation-plan.md`; fill empty placeholders (`session-rules.md`,
  `agent-workflows.md`) or delete them.
- **Why now:** docs are the shared brain across short, context-limited sessions.
- **Dependencies:** the locked SPEC.
- **Complexity:** M
- **Deliverables:** the docs above (one agent per file).
- **Acceptance:** every doc cross-links correctly; no empty non-placeholder files
  remain; scope authority and contracts are consistent across docs.
- **Status:** done (session 1)

---

## Phase 1 — Foundations (the spine that everything hangs on)

Goal: an empty-but-running stack — api answers `/healthz`, worker polls an empty
queue, frontend renders a shell, `make dev` boots all four services. No pipeline
logic yet.

### P1.1 — Backend config
- **Goal:** `app/config.py` — pydantic-settings `Settings` reading the locked env
  vars (`DATABASE_URL`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `DRY_RUN`=true,
  `PROMPT_COUNT`=10, `PANEL_ENGINES`, `MAX_RESPONSES_PER_JOB`=60,
  `WORKER_POLL_SECONDS`=2, `STALE_CLAIM_SECONDS`=300) with the SPEC defaults.
- **Why now:** every other backend module imports settings.
- **Dependencies:** `pyproject.toml` deps present.
- **Complexity:** S
- **Deliverables:** `backend/app/config.py`, `backend/app/__init__.py`.
- **Acceptance:** importing `settings` with no env set yields the documented
  defaults; `DRY_RUN` defaults **true** (safe by default).
- **Status:** done (session 1)

### P1.2 — DB base, models, session
- **Goal:** SQLAlchemy 2.0 models for `analyses`, `prompts`, `responses`,
  `llm_cache` per the locked schema; session factory; SQLite-compatible column
  choices (so unit tests run in-memory — see [test-suite.md](test-suite.md) §3.3).
- **Why now:** the queue, services, and pipeline all read/write these tables.
- **Dependencies:** P1.1.
- **Complexity:** M
- **Deliverables:** `backend/app/db/{base.py,models.py,session.py}`.
- **Acceptance:** models create cleanly on both SQLite and Postgres; UUID pks
  default to `uuid4`; timestamps are timezone-aware.
- **Status:** done (session 1)

### P1.3 — Alembic initial migration
- **Goal:** one migration creating all four tables + the `llm_cache.cache_key`
  unique index.
- **Why now:** `make migrate` and the deploy flow need a real schema.
- **Dependencies:** P1.2.
- **Complexity:** S
- **Deliverables:** `backend/alembic/**` (env + one revision).
- **Acceptance:** `alembic upgrade head` on a fresh Postgres creates the four
  tables; `downgrade base` drops them.
- **Status:** done (session 1)

### P1.4 — Postgres-as-queue
- **Goal:** `app/jobs/queue.py` — claim one job in a single transaction
  (`status='queued' OR (running AND claimed_at < now()-STALE_CLAIM_SECONDS)`,
  `ORDER BY created_at LIMIT 1 FOR UPDATE SKIP LOCKED`), set `running`,
  `claimed_at=now()`, `attempts+=1`; `attempts>3 → failed`; a heartbeat helper to
  bump `claimed_at` between steps.
- **Why now:** the worker's correctness (NFR-3: never lose or double-run) lives
  here.
- **Dependencies:** P1.2.
- **Complexity:** M
- **Deliverables:** `backend/app/jobs/queue.py`.
- **Acceptance:** two concurrent claimers never grab the same row; a stale
  `running` row is reclaimed; `attempts>3` flips to `failed` with
  `error='max retries exceeded'`.
- **Status:** done (session 1)

### P1.5 — API layer + service glue
- **Goal:** `app/api/{main,routes,schemas}.py` + `app/services/analyses.py`
  implementing the locked contract: `GET /healthz`; `POST /api/v1/analyses`
  (valid → **202** `{id}`, invalid → **422**); `GET /api/v1/analyses/{id}` (full
  envelope with `result` **always present**, inner fields null until produced,
  unknown id → 404). Progress/step mapping per SPEC.
- **Why now:** it is the FE/BE contract surface and the entry point for the whole
  loop (FR-1, FR-2, FR-7).
- **Dependencies:** P1.2, P1.4.
- **Complexity:** M
- **Deliverables:** `backend/app/api/{main.py,routes.py,schemas.py}`,
  `backend/app/services/analyses.py`.
- **Acceptance:** matches the API contract exactly (see
  [architecture.md](architecture.md)); `app.openapi()` is exportable for
  `make gen-types`.
- **Status:** done (session 1)

### P1.6 — Worker skeleton
- **Goal:** `app/worker.py` — `while True` loop: claim a job (P1.4), run the
  pipeline (stubbed call for now — real steps land in P2.9), `time.sleep(POLL)`;
  on any exception mark `failed` with `str(exc)` truncated to 500 chars, partial
  rows kept.
- **Why now:** proves the queue drains; P2.9 fills in the real pipeline call.
- **Dependencies:** P1.4, P1.5.
- **Complexity:** S
- **Deliverables:** `backend/app/worker.py`.
- **Acceptance:** worker starts, claims a queued row, marks it `running` then
  `done` (stub), sleeps, repeats; a raised exception marks the job `failed`
  without crashing the loop.
- **Status:** done (session 1)

### P1.7 — Frontend scaffold + brand tokens
- **Goal:** Next.js 15 App Router + TS + Tailwind scaffold; copy the
  [frontend-brandkit.md](frontend-brandkit.md) §2 tokens into the Tailwind config;
  `next.config` `rewrites()` proxying `/api/:path*` and `/healthz` to
  `API_ORIGIN` (default `http://localhost:8141`) so there is **no CORS** and FE
  fetches relative paths only.
- **Why now:** the three screens (P3.x) need a themed shell and the proxy.
- **Dependencies:** none (contract-only dependency on the API shape).
- **Complexity:** M
- **Deliverables:** `frontend/` scaffold, `tailwind.config`, `next.config`,
  `package.json` with the locked deps.
- **Acceptance:** `npm run dev` serves a themed placeholder on `:8140`;
  `/healthz` proxies to the api; brand tokens resolve in Tailwind classes.
- **Status:** done (session 1)

### P1.8 — Compose + Makefile + Dockerfile + env example
- **Goal:** the single control panel. `deploy/docker-compose.yml` (db + api +
  worker + web, bind-mount hot reload); one backend `Dockerfile`
  (`python:3.12-slim` + `uv sync`, `CMD uvicorn app.api.main:app`) run as both api
  and worker; `Makefile` targets per the README contract; `deploy/.env.example`
  (all config vars + `POSTGRES_PASSWORD`, `DRY_RUN=1` default, commented, **no
  real keys**).
- **Why now:** `make dev` is the definition-of-done boot command.
- **Dependencies:** P1.1–P1.7 (services to compose).
- **Complexity:** M
- **Deliverables:** `deploy/docker-compose.yml`, `backend/Dockerfile`, `Makefile`,
  `deploy/.env.example`, `scripts/` bootstrap helpers.
- **Acceptance:** `make dev` boots all four services with hot reload; `make help`
  lists every target in the README table; `make migrate` runs against the db
  container.
- **Status:** done (session 1)

---

## Phase 2 — Core MVP (the GEO engine)

Goal: the six pipeline steps + providers, each unit-tested at $0 under
`DRY_RUN=1`, wired into the worker so a claimed job runs end-to-end and persists
partial results after every step (FR-3–FR-5, FR-8). Build test-first
([test-suite.md](test-suite.md) §8).

### P2.1 — Provider interface + mock + registry
- **Goal:** `providers/base.py` (`Provider` Protocol: `name`, `model`,
  `generate(prompt) -> ProviderResult(text, model, cost_usd)`); `providers/mock.py`
  (deterministic — mentions company iff `sha256(prompt).digest()[0] % 2 == 0`,
  cost 0); `providers/registry.py` (`get_panel` → 4 `MockProvider`s when
  `DRY_RUN`, else map `PANEL_ENGINES`; `get_analysis_provider` for the KYC call).
- **Why now:** every downstream step and test depends on the mock + registry.
- **Dependencies:** P1.1.
- **Complexity:** M
- **Deliverables:** `backend/app/providers/{base.py,mock.py,registry.py}`.
- **Acceptance:** `DRY_RUN=1` yields four mocks named after the panel engines; the
  mock is deterministic and free; registry is the single provider entry point.
- **Status:** done (session 1)

### P2.2 — Real + stub providers
- **Goal:** `anthropic_provider.py` (real, `claude-haiku-4-5-20251001`, anthropic
  SDK, `max_tokens=1024`, cost = tokens × a price-table constant);
  `openai_provider.py` (real, `gpt-4o-mini`, openai SDK); `gemini_provider.py` +
  `perplexity_provider.py` (STUBS: canned plausible answer that *sometimes
  mentions nothing*, model `"stub"`, cost 0).
- **Why now:** completes the panel shape; real adapters are exercised only via
  `respx` in tests (never a live call — [test-suite.md](test-suite.md) §1).
- **Dependencies:** P2.1.
- **Complexity:** M
- **Deliverables:** `backend/app/providers/{anthropic_provider,openai_provider,gemini_provider,perplexity_provider}.py`.
- **Acceptance:** each satisfies the `Provider` protocol; real adapters unit-test
  their HTTP shape under `respx`; stubs return `cost_usd=0`, model `"stub"`.
- **Status:** done (session 1)

### P2.3 — Discovery
- **Goal:** `pipeline/discovery.py` `discover(url) -> str`: httpx GET (15s timeout,
  UA `YankiBot/0.1`), BeautifulSoup parse, drop script/style/nav, homepage text +
  up to 5 same-domain links, cap ~20k chars; unreachable/empty →
  `PipelineError("could not read the site")`.
- **Why now:** step 1 of the loop; feeds KYC.
- **Dependencies:** P1.1.
- **Complexity:** M
- **Deliverables:** `backend/app/pipeline/discovery.py`, `pipeline/errors.py`
  (`PipelineError`).
- **Acceptance:** reachable page → non-empty text; unreachable → `PipelineError`,
  no crash (test-suite §3.2, via `respx`).
- **Status:** done (session 1)

### P2.4 — KYC
- **Goal:** `pipeline/kyc.py` `generate_kyc(text, url, provider) -> KYC`: one LLM
  call for strict JSON; strip ```json fences; validate against Pydantic `KYC`
  (company, description, industry, aliases — always include company name +
  registrable domain without TLD; products/services/keywords/locations/
  competitors default `[]`).
- **Why now:** step 2; its output drives prompt generation and footprint aliases.
- **Dependencies:** P2.1.
- **Complexity:** M
- **Deliverables:** `backend/app/pipeline/kyc.py`, the `KYC` model.
- **Acceptance:** given canned model output, parses + validates; `aliases`
  contains the company name and the domain name (test-suite §3.2).
- **Status:** done (session 1)

### P2.5 — Prompts (deterministic templates)
- **Goal:** `pipeline/prompts.py` `generate_prompts(kyc, count) ->
  list[PromptSpec]`: cycle categories (recommendation / comparison / alternatives
  / best-of / use-case), fill from KYC, no LLM. Exactly `count`, all non-empty, no
  duplicates.
- **Why now:** step 3; pure + free + the widest unit-test surface.
- **Dependencies:** P2.4 (`KYC` shape).
- **Complexity:** S
- **Deliverables:** `backend/app/pipeline/prompts.py`, `PromptSpec`.
- **Acceptance:** exactly `count` specs, each non-empty with a category, no dupes
  (test-suite §3.2). Aim ~100% branch coverage.
- **Status:** done (session 1)

### P2.6 — Execute (fan-out + llm_cache)
- **Goal:** `pipeline/execute.py`: for each prompt × each panel engine, consult
  `llm_cache` (fresh <24h) else call the provider, then insert a `responses` row
  and a cache row; enforce `MAX_RESPONSES_PER_JOB` (stop + log); persist after each
  response (crash-safe).
- **Why now:** step 4; the cost-control + audit-trail heart (FR-4, FR-8).
- **Dependencies:** P2.1, P2.5, P1.2.
- **Complexity:** L
- **Deliverables:** `backend/app/pipeline/execute.py`.
- **Acceptance:** one `responses` row per engine per prompt; a warm cache means no
  second provider call; `MAX_RESPONSES_PER_JOB` never exceeded (test-suite §3.2).
- **Status:** done (session 1)

### P2.7 — Footprint
- **Goal:** `pipeline/footprint.py` `detect(raw_text, kyc) -> (bool, snippet|None)`:
  pure, deterministic, case-insensitive search over company/aliases/domain; on hit
  return a ±60-char snippet around the first match; no LLM.
- **Why now:** step 5; the "show our work" evidence (FR-5).
- **Dependencies:** P2.4 (`KYC`).
- **Complexity:** S
- **Deliverables:** `backend/app/pipeline/footprint.py`.
- **Acceptance:** present → `(True, snippet)`; absent → `(False, None)`;
  deterministic (test-suite §3.2). Aim ~100% branch coverage.
- **Status:** done (session 1)

### P2.8 — Scoring
- **Goal:** `pipeline/scoring.py` `geo_score(footprints, total) -> float`: pure;
  `0.0` when `total==0` (ADR-11, no divide-by-zero).
- **Why now:** step 6; the number the whole product sells (must be provably
  correct).
- **Dependencies:** none.
- **Complexity:** S
- **Deliverables:** `backend/app/pipeline/scoring.py`.
- **Acceptance:** `score == footprints/total`; `total==0` → `0.0` (test-suite
  §3.2). Aim 100% coverage.
- **Status:** done (session 1)

### P2.9 — Pipeline orchestrator (wire into worker)
- **Goal:** a `run_pipeline(session, analysis_id, settings)` entry point that runs
  discovery → kyc → prompts → execute → footprint → scoring in order, updating
  `status`/`progress`/`current_step` per the SPEC mapping (15/30/45/80/90/100),
  heart-beating `claimed_at`, persisting each step's output; the P1.6 worker calls
  it.
- **Why now:** turns six modules into the running loop; the seam pipeline ↔
  backend-spine must agree on.
- **Dependencies:** P2.3–P2.8, P1.6.
- **Complexity:** M
- **Deliverables:** `backend/app/pipeline/runner.py` (`run_pipeline`); worker
  wiring (backend-spine imports it).
- **Acceptance:** a claimed job walks all six steps, advances progress correctly,
  and lands `done` at 100 under `DRY_RUN=1`; any step exception → `failed`, partial
  rows kept (FR-7).
- **Status:** done (session 1)

### P2.10 — Backend tests
- **Goal (a, backend-spine):** `tests/conftest.py` (client, db_session, pg_engine
  auto-skip, mock_provider fixtures), `tests/test_api.py` (Submit + Results rows),
  `tests/test_queue.py` (claim / stale-reaper / `attempts>3` on SQLite), and
  `tests/test_queue_postgres.py` (the Postgres-only `FOR UPDATE SKIP LOCKED`
  concurrency guard — runs only when `TEST_DATABASE_URL` points at a live
  Postgres, else skips).
  **Goal (b, pipeline):** `tests/pipeline/conftest.py` (sample_kyc, sample_html) +
  one test file per step per the acceptance→test map.
- **Why now:** TDD is how each step is built; `make test` must be green at
  session end.
- **Dependencies:** the code each test covers.
- **Complexity:** L
- **Deliverables:** `backend/tests/**` (split by ownership above).
- **Acceptance:** a test exists for every [02-mvp.md §8](02-mvp.md) acceptance row
  ([test-suite.md](test-suite.md) §9); `make test` green; DB tests auto-skip with
  no Postgres.
- **Status:** done (session 1)

---

## Phase 3 — Usable MVP (the three screens, wired end-to-end)

Goal: a human submits a URL at `:8140` and watches the six steps render into a
GEO score with every raw answer behind it — the whole-loop definition of done.

### P3.1 — API client + generated types (contract)
- **Goal:** `lib/api.ts` (thin fetch wrapper over relative `/api/v1/...`);
  `make gen-types` runs `scripts/gen_openapi.py` to export `app.openapi()` →
  `shared/contracts/openapi.json`, then `openapi-typescript` →
  `frontend/lib/types.ts` (both checked in, never hand-edited). The app never
  imports `types.ts` directly: `lib/contracts.ts` is a hand-maintained seam that
  re-exports the generated `components['schemas']` under friendly names
  (`Analysis`, `Prompt`, …) and narrows the free-form fields (`status`,
  `current_step`, `kyc`) to their locked SPEC shapes.
- **Why now:** the FE/BE contract cannot silently drift (NFR-6); the screens type
  against `contracts.ts`, which is anchored to the generated types.
- **Dependencies:** P1.5 (openapi export), P1.7.
- **Complexity:** M
- **Deliverables:** `frontend/lib/{api.ts,types.ts,contracts.ts}`,
  `scripts/gen_openapi.py`, `shared/contracts/openapi.json`.
- **Acceptance:** `make gen-types` regenerates both artifacts byte-stably; a
  contract change shows up as a diff (CI drift gate is P4.3); `contracts.ts`
  compiles against the regenerated `types.ts`.
- **Status:** done (session 1)

### P3.2 — Landing page + UrlForm
- **Goal:** `/` with headline "See how AI answers talk about your brand." and a
  `UrlForm` that validates client-side and POSTs to create an analysis, then
  routes to `/analyses/[id]`.
- **Why now:** the entry screen (FR-6).
- **Dependencies:** P3.1, brandkit components.
- **Complexity:** S
- **Deliverables:** `frontend/app/page.tsx`,
  `frontend/components/{Button,UrlForm}.tsx`.
- **Acceptance:** blank/malformed URL rejected client-side (no submit fires); a
  valid `https://…` submits and navigates.
- **Status:** done (session 1)

### P3.3 — Progress + results screen
- **Goal:** `/analyses/[id]` polls `GET` every 2s. queued/running →
  `StepProgress` (six steps from `current_step`+`progress`). done → `ScoreGauge`
  + `ResultsTable` + KYC JSON block + prompts list. failed → danger card with
  `error` + retry link.
- **Why now:** the live-progress + results screen — the payoff (FR-6, FR-7).
- **Dependencies:** P3.1, P3.2.
- **Complexity:** M
- **Deliverables:** `frontend/app/analyses/[id]/page.tsx`,
  `frontend/components/{StepProgress,ScoreGauge,ResultsTable}.tsx`.
- **Acceptance:** all three states render from the real envelope; the gauge
  exposes an aria-label describing the score.
- **Status:** done (session 1)

### P3.4 — Frontend component tests
- **Goal:** vitest + testing-library for `UrlForm` validation, `ScoreGauge`
  aria-label, and the `lib/score.ts` score→color-band helper (mock `lib/api.ts`,
  no network).
- **Why now:** the UI rows of the acceptance→test map (test-suite §9).
- **Dependencies:** P3.2, P3.3.
- **Complexity:** S
- **Deliverables:** `frontend/tests/{UrlForm,ScoreGauge}.test.tsx`,
  `frontend/tests/score.test.ts`, and `frontend/lib/score.ts` (the color-band
  helper under test).
- **Acceptance:** `npm test -- --run` green (9 vitest tests); the three
  logic-bearing units have a test each.
- **Status:** done (session 1)

### P3.5 — Playwright happy path + DRY_RUN e2e verification
- **Goal:** `e2e/happy-path.spec.ts` (submit `https://example.com` against a
  running `DRY_RUN=1` stack → six steps → assert a score renders; **gated on
  `E2E_BASE_URL`**, skipped otherwise). Then manually verify the full loop against
  `make dev`.
- **Why now:** the whole-MVP acceptance (02-mvp.md §8 last row); proves the
  session's definition of done.
- **Dependencies:** P2.9, P3.3, P1.8.
- **Complexity:** M
- **Deliverables:** `frontend/e2e/happy-path.spec.ts`,
  `frontend/playwright.config.ts`.
- **Acceptance:** with a booted DRY_RUN stack and `E2E_BASE_URL` set, the spec
  passes; unset → skipped (keeps `make test` fast + hermetic).
- **Status:** done (session 1) — spec authored and the full loop **manually**
  verified end-to-end against a live DRY_RUN stack. The automated Playwright run
  was skipped in this env (chromium needs a root `install-deps`); running it in
  CI is P4.4.

---

## Phase 4 — Polish (pending — later sessions)

Goal: take the working DRY_RUN loop to a live, cost-validated, CI-guarded deploy,
then start the first [roadmap.md](roadmap.md) **Next** items. Each task is sized
for one focused agent session. **Do not start any Phase-4 task until the Phase-3
happy path renders a score.**

### P4.1 — Real-key smoke test + Week-1 invoice check
- **Goal:** run one real analysis with `DRY_RUN=0` and real Anthropic + OpenAI
  keys (Gemini/Perplexity stay stubbed); confirm responses, footprints, and a
  score; capture the actual per-analysis cost and check it against the caps
  (NFR-1). Record the number for the pricing decision in
  [roadmap.md](roadmap.md) 2d.
- **Why now:** validates the cost model before anything goes public; the one thing
  DRY_RUN cannot prove.
- **Dependencies:** all of Phase 3 green.
- **Complexity:** S
- **Deliverables:** a cost note (in the session summary / feasibility doc), no
  code unless a bug surfaces.
- **Acceptance:** a real run completes within the caps; the measured cost is
  recorded; no secret is committed.
- **Status:** todo

### P4.2 — Deploy to test.beyondkaira.com
- **Goal:** finish and exercise the ams-pulse-style `deploy/` scripts (build, tag
  by git SHA, `compose -p yanki-prod up`, `/healthz` check, rollback to a
  last-good-SHA file); drop the Caddy import snippet; first real deploy.
- **Why now:** turns "runs on my laptop" into a shareable URL for design partners.
- **Dependencies:** P1.8, P4.1.
- **Complexity:** M
- **Deliverables:** `deploy/{deploy.sh,rollback.sh,...}`,
  `deploy/caddy/test.beyondkaira.com.caddy`, README deploy section verified.
- **Acceptance:** `make deploy` builds, migrates, health-checks, and serves
  `https://test.beyondkaira.com`; `make rollback` restores the last-good SHA.
  (Scripts are currently marked UNTESTED tech debt — this task clears that.)
- **Status:** todo

### P4.3 — CI hardening
- **Goal:** GitHub Actions: `make lint` + `make typecheck` + `make test` (with a
  Postgres service so DB tests actually run), an **OpenAPI drift gate** (fail if
  `make gen-types` produces a diff — NFR-6), and **gitleaks** in pre-commit + CI
  (NFR-5).
- **Why now:** locks in the contract-safety and secret-safety guarantees before
  more hands touch the repo.
- **Dependencies:** P2.10, P3.1.
- **Complexity:** M
- **Deliverables:** `.github/workflows/ci.yml`, `.pre-commit-config.yaml`,
  gitleaks config.
- **Acceptance:** CI runs the full suite green on a clean PR, red on a contract
  drift or a planted secret.
- **Status:** todo

### P4.4 — Playwright in CI
- **Goal:** a CI job that boots the `DRY_RUN=1` stack, sets `E2E_BASE_URL`, and
  runs `e2e/happy-path.spec.ts`.
- **Why now:** guards the whole-loop against regressions once it's shared.
- **Dependencies:** P3.5, P4.3.
- **Complexity:** S
- **Deliverables:** an e2e job in `.github/workflows/`.
- **Acceptance:** the happy path runs (not skipped) and passes in CI.
- **Status:** todo

### P4.5 — Accessibility + polish audit
- **Goal:** audit the three screens against [frontend-brandkit.md](frontend-brandkit.md)
  §7 (contrast, focus states, aria, keyboard nav, reduced-motion) and fix gaps;
  tidy loading/empty/error states.
- **Why now:** the checker is a public marketing surface — accessibility is table
  stakes before launch.
- **Dependencies:** Phase 3 green.
- **Complexity:** M
- **Deliverables:** frontend fixes; a short audit note.
- **Acceptance:** the §7 checklist passes; no critical axe violations on the three
  screens.
- **Status:** todo

### P4.6 — Kick off roadmap "Next" (free public checker)
- **Goal:** the first [roadmap.md](roadmap.md) **Next** slice — begin 2a (public
  no-signup checker: brand + category → fixed prompts × 4 engines, cached 24h,
  rate-limited, email-gated). Break it into P5.x tasks in a follow-up session.
- **Why now:** the checker is the demand test and launch wedge; it ships weeks
  before the app.
- **Dependencies:** all of Phase 4 above; a green, deployed MVP.
- **Complexity:** L (multi-session — decompose first)
- **Deliverables:** a new **Phase 5** task breakdown in this doc; no build until
  decomposed.
- **Acceptance:** Phase 5 tasks exist, each session-sized; scope stays frozen per
  02-mvp.md §4 until the MVP is signed off.
- **Status:** todo

---

## Technical debt & assumptions (living list)

Keep this honest — see [design.md](design.md) ADR log for the "why" behind
decisions.

- **Deploy/rollback scripts are UNTESTED** until P4.2. Marked so in README.
- **Gemini + Perplexity are stubs** (planned — roadmap 2b), not a shortcut to hide.
- **Prompt generation is templated, not LLM** (deliberate — testable + free;
  roadmap 2d LLM prompt engine supersedes).
- **`llm_cache` is within-job only** for the MVP; the cross-account cache (the real
  cost lever) is roadmap 2d.
- **Real-key cost is unvalidated** until P4.1 — the biggest open risk to the
  pricing story.
- **Assumption:** SQLite covers unit tests and Postgres covers queue/jsonb
  tests; if a model needs a Postgres-only type in a hot path, revisit P1.2.
</content>
