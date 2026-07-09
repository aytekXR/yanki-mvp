# Yanki — Test Suite

*Audience: every engineer. This document is how ["done" from the MVP PRD](02-mvp.md)
is **verified**. It covers the test pyramid, the TDD workflow, fixtures, the
$0-cost rule, how to run everything, and the acceptance-criteria → test-file map.*

See also: [02-mvp.md](02-mvp.md) (scope + acceptance criteria — the "what"),
[architecture.md](architecture.md) (how it's built).

---

## 1. The golden rule: tests cost $0

**CI and the test suite NEVER call a paid API.** Every test runs against the
deterministic `MockProvider` (or a `respx`-mocked HTTP layer). This is not a
nicety — it is a hard constraint (NFR-1). Two mechanisms enforce it:

- **`DRY_RUN=1`** (the default in config) makes `providers/registry.py` hand
  back four `MockProvider`s instead of real Anthropic/OpenAI clients. The mock
  is deterministic: it mentions the company iff `sha256(prompt).digest()[0] % 2
  == 0`, and always reports `cost_usd = 0`.
- **`respx`** intercepts any real `httpx` call in the rare unit test that
  exercises a real provider adapter, so no network request ever leaves.

If a test needs a real key to pass, it is a bug in the test. Never put a real
key in a fixture, an env file, or CI.

---

## 2. The test pyramid

We keep the classic shape: many fast unit tests at the base, a middle band of
API/integration tests, and a single thin end-to-end happy path at the top.

```
        ┌───────────────────────────┐
        │   e2e (Playwright) ×1      │   happy path, gated on E2E_BASE_URL
        ├───────────────────────────┤
        │  API tests (TestClient)   │   FastAPI routes, in-process
        │  component tests (vitest) │   React components, jsdom
        ├───────────────────────────┤
        │      unit (pytest)        │   pure functions: scoring, footprint,
        │   ← the widest layer →    │   prompts, KYC parsing, mock provider
        └───────────────────────────┘
```

| Layer | Tool | Runs against | Speed | Count |
|---|---|---|---|---|
| Backend unit | pytest | pure functions, no I/O | ms | most tests |
| Backend API | pytest + FastAPI `TestClient` | in-process app, SQLite or Postgres | fast | one file |
| Backend DB/queue | pytest + `TEST_DATABASE_URL` | real Postgres (auto-skips if down) | medium | one file |
| Frontend component | vitest + testing-library | React in jsdom | fast | per component |
| End-to-end | Playwright | a running `DRY_RUN=1` stack | slow | one spec |

**Why the base is so wide:** the whole GEO engine is built from pure, sync
functions (`scoring`, `footprint`, `prompts`, plus KYC JSON parsing). Pure
functions are the cheapest possible thing to test — no DB, no network, no mocks
beyond a fake provider — so they carry the bulk of our confidence.

---

## 3. Backend testing (pytest)

### 3.1 Layout

```
backend/tests/
├── conftest.py            # shared fixtures (app client, db session, mock provider)
├── test_api.py            # POST/GET routes via TestClient
├── test_queue.py          # claim / stale-reaper / retry logic (needs Postgres)
└── pipeline/
    ├── conftest.py        # pipeline-only fixtures (sample KYC, sample HTML)
    ├── test_discovery.py
    ├── test_kyc.py
    ├── test_prompts.py
    ├── test_execute.py
    ├── test_footprint.py
    └── test_scoring.py
```

Ownership note: `tests/conftest.py`, `test_api.py`, `test_queue.py` belong to the
**backend-spine** agent; everything under `tests/pipeline/` (including its own
`conftest.py`) belongs to the **pipeline** agent.

### 3.2 What each layer tests

**Pure-function unit tests** (`pipeline/test_scoring.py`,
`test_footprint.py`, `test_prompts.py`) — no fixtures beyond plain Python data.
Feed input, assert output. These are the red-green heart of the TDD loop.

- `scoring`: `geo_score(footprints, total)` equals `footprints / total`; and
  `total == 0` returns `0.0` (no `ZeroDivisionError`) — ADR-11.
- `footprint`: `detect(raw_text, kyc)` returns `(True, snippet)` when the
  brand/alias/domain appears (case-insensitive), `(False, None)` otherwise, and
  is fully deterministic (same input → same output). Snippet is ±60 chars.
- `prompts`: `generate_prompts(kyc, count)` returns exactly `count` specs, every
  `text` non-empty, every spec has a `category`, no duplicates.

**Provider-mocked tests** (`test_kyc.py`, `test_execute.py`) — inject a
`MockProvider` (or `respx` for the real adapter's HTTP shape). Never hit a
network.

- `kyc`: given canned model output, `generate_kyc(...)` strips ```json fences,
  parses, and validates against the `KYC` Pydantic model; `aliases` always
  includes the company name and the registrable domain name.
- `execute`: each prompt × each panel engine yields one `responses` row; the
  `llm_cache` is consulted before each provider call (a warm cache means no
  second call); `MAX_RESPONSES_PER_JOB` is never exceeded.

**Discovery test** (`test_discovery.py`) — use `respx` to serve fake HTML;
assert extracted text is non-empty for a reachable page and that an unreachable
site raises `PipelineError("could not read the site")` (a clean failure, not a
crash).

**API tests** (`test_api.py`) — FastAPI `TestClient`, in-process, no running
server:
- valid URL → `202` + `{"id": ...}`, and the row exists with `status=queued`;
- invalid/missing URL → `422`;
- `GET` unknown id → `404`;
- `GET` a known id → the full envelope with `result` always present (inner
  fields null until produced).

**Queue tests** (`test_queue.py`) — the Postgres-as-queue mechanics: one worker
claims a `queued` row via `FOR UPDATE SKIP LOCKED`; a stale `running` row
(`claimed_at` older than `STALE_CLAIM_SECONDS`) is reclaimed; `attempts > 3`
flips the job to `failed` with `error='max retries exceeded'`.

### 3.3 SQLite for unit, Postgres for the queue

Models are written to be **SQLite-compatible** so most tests run against an
in-memory SQLite database with zero external services — instant, hermetic,
CI-friendly. The tests that genuinely need Postgres semantics
(`FOR UPDATE SKIP LOCKED`, jsonb, `timestamptz`) live in `test_queue.py` and use
`TEST_DATABASE_URL`.

**Auto-skip when Postgres is unreachable.** DB-dependent tests attempt a
connection in a fixture; if it fails, they `pytest.skip(...)` rather than error.
So a laptop with no Docker still gets a green (mostly-run) suite, and CI — which
does start Postgres — runs them for real.

```python
# conftest.py sketch
@pytest.fixture(scope="session")
def pg_engine():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL not set")
    engine = create_engine(url)
    try:
        engine.connect().close()
    except OperationalError:
        pytest.skip("Postgres unreachable — skipping DB tests")
    return engine
```

---

## 4. Frontend testing (vitest + testing-library)

```
frontend/
├── components/*.test.tsx     # co-located with each component
└── e2e/happy-path.spec.ts    # Playwright
```

Vitest + `@testing-library/react` render components into **jsdom** — no browser,
no network. The three components with real logic get real tests:

- **`UrlForm`** — validation: a blank or malformed URL is rejected client-side
  and no submit fires; a valid `https://…` URL submits.
- **`ScoreGauge`** — accessibility: exposes a correct `aria-label` describing the
  score (e.g. `"GEO score 45%"`), so screen readers and tests can read it.
- **Score color scale** — the score → color mapping (the gauge's visual band) is
  a pure helper; assert the boundaries of the scale map to the expected colors.

Anything that talks to the API is tested by mocking `lib/api.ts`, never by
hitting a backend. Fast, deterministic, offline.

---

## 5. End-to-end (Playwright)

One spec — `e2e/happy-path.spec.ts` — proves the whole loop renders:

1. open the landing page, submit `https://example.com`;
2. land on `/analyses/{id}`, watch the six steps advance;
3. assert a **score renders** on the results screen.

It runs against a real, already-running stack in `DRY_RUN=1` mode (so it costs
$0 and is deterministic). It is **gated on `E2E_BASE_URL`**: if that env var is
unset, the spec is skipped. This keeps `make test` fast and hermetic while
letting CI (or a dev) point Playwright at a booted stack on demand.

---

## 6. How to run it

```bash
make test      # backend (pytest) + frontend (vitest --run). The everyday command.
make e2e       # Playwright happy path (needs E2E_BASE_URL → a DRY_RUN=1 stack)
```

What `make test` does under the hood:

1. If Docker is present, start a throwaway Postgres container and export
   `TEST_DATABASE_URL` (port **5433**, so it never collides with a dev DB on
   5432).
2. `uv run pytest` — DB-dependent tests run against that container; if Docker is
   absent they auto-skip (§3.3).
3. `npm test -- --run` — vitest, single-shot (no watch).

`make test` is the same command CI runs, so "green on my machine" means "green in
CI" (modulo the DB tests, which CI always exercises because it always has
Postgres).

To run one slice while developing:

```bash
uv run pytest backend/tests/pipeline/test_scoring.py -q   # one file
uv run pytest -k footprint                                 # by name
npm test -- --run ScoreGauge                               # one component
```

---

## 7. Fixtures

Keep fixtures small, deterministic, and free. The important ones:

| Fixture | Where | What it gives you |
|---|---|---|
| `client` | `tests/conftest.py` | a FastAPI `TestClient` bound to a fresh SQLite DB |
| `db_session` | `tests/conftest.py` | a SQLAlchemy session on an in-memory SQLite schema, rolled back per test |
| `pg_engine` | `tests/conftest.py` | a real-Postgres engine from `TEST_DATABASE_URL`, or `skip` if unreachable |
| `mock_provider` | `tests/conftest.py` | a `MockProvider` instance for deterministic, $0 generation |
| `sample_kyc` | `tests/pipeline/conftest.py` | a valid `KYC` object (company, aliases, industry, …) |
| `sample_html` | `tests/pipeline/conftest.py` | a small HTML page for discovery/BeautifulSoup tests |

Frontend fixtures are just plain TS factory functions (e.g. a `makeAnalysis()`
returning a done-state envelope) mocked into `lib/api.ts`. No shared fixture
server.

Because the mock provider and the templated prompt generator are deterministic,
the same inputs always produce the same outputs — tests assert exact values, not
"roughly".

---

## 8. TDD workflow (red → green)

The pipeline steps are built test-first. The loop:

1. **Red** — write a failing test named after the acceptance criterion for the
   step (§9). Run it; watch it fail for the right reason.
2. **Green** — write the smallest code that makes it pass.
3. **Refactor** — clean up with the test as your safety net.

**Test names mirror acceptance criteria** so the suite reads like the PRD. For
example, from the Scoring row:

```python
def test_geo_score_is_footprints_over_total(): ...
def test_geo_score_zero_total_does_not_divide_by_zero(): ...
```

and from Footprint:

```python
def test_footprint_true_with_matched_snippet_when_brand_present(): ...
def test_footprint_false_and_null_snippet_when_absent(): ...
def test_footprint_is_deterministic(): ...
```

Reading the test names top to bottom should tell you what the step promises. The
pure-function steps (scoring, footprint, prompts) are the easiest place to work
this way and where the discipline pays off most.

---

## 9. Acceptance criteria → test files

Every row of [02-mvp.md §8](02-mvp.md) maps to at least one test. The coverage
bar for the MVP is **"a test exists for every acceptance row"**, not a percentage
gate (§10).

| Acceptance step | Primary test file(s) | Key assertions |
|---|---|---|
| **Submit** | `tests/test_api.py` | valid URL → `202`+`id`, row is `queued`; invalid → `422` |
| **Discovery** | `tests/pipeline/test_discovery.py` | reachable → non-empty text; unreachable → `PipelineError`, no crash |
| **KYC** | `tests/pipeline/test_kyc.py` | output validates against `KYC`; company/industry/aliases populated |
| **Prompts** | `tests/pipeline/test_prompts.py` | exactly `PROMPT_COUNT`; each has non-empty `text` + `category`; no dupes |
| **Execution** | `tests/pipeline/test_execute.py` | one response per engine per prompt; cache consulted; `MAX_RESPONSES_PER_JOB` respected |
| **Footprint** | `tests/pipeline/test_footprint.py` | present → `true`+snippet; absent → `false`/null; deterministic |
| **Scoring** | `tests/pipeline/test_scoring.py` | `score == footprints/total`; `total==0` safe |
| **Results (API)** | `tests/test_api.py` | `GET` returns KYC + prompts + responses + score; `result` always present |
| **Results (UI)** | `frontend/components/ScoreGauge.test.tsx`, `ResultsTable.test.tsx`, `UrlForm.test.tsx` | gauge aria-label + color scale; form validation; table renders rows |
| **Whole-MVP happy path** | `frontend/e2e/happy-path.spec.ts` | submit → six steps → a score renders (DRY_RUN=1) |
| *(supporting)* Queue reliability (NFR-3) | `tests/test_queue.py` | claim / stale-reaper / `attempts>3 → failed` |

---

## 10. Coverage targets (pragmatic, not dogmatic)

We do **not** gate CI on a global coverage percentage — that tends to reward
testing trivia and punish honest, hard-to-test glue. Instead:

- **Pipeline pure functions** (`scoring`, `footprint`, `prompts`, KYC parsing):
  aim for **~100%** line + branch coverage. They are small, pure, and the core of
  the product's credibility ("show your work") — there is no excuse for a
  missed branch here.
- **Everywhere else:** the bar is **"a test exists for every acceptance-criteria
  row" (§9)**. If a row has no test, that is the gap to close — not a number on a
  dashboard.

This matches the MVP ethos: boring, minimal, junior-readable tests that
correspond one-to-one with what we promised to ship.
