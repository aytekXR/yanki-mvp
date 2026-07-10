# Yanki

**Yanki measures how visible a company is across generative-AI answers.**
You submit a company website URL; a background job crawls the site, builds a
structured company profile (KYC JSON), generates prompts, runs them across
multiple AI models, checks whether the company is mentioned, and computes a
primitive **GEO score** (mentions ÷ total responses). Long-term goal: an
affordable, transparent Semrush alternative for AI-answer rank tracking.

This README is the front door. It gets a new engineer from `git clone` to a
running local stack in about five minutes. Deeper docs live in [`docs/`](#documentation).

---

## Quickstart (about 5 minutes)

Prerequisites: **Docker + Compose v2**, **Python 3.12**, **Node 20+ (22 LTS recommended)**.
(`make setup` installs everything else — `uv`, backend/frontend deps, pre-commit.)

```bash
# 1. Clone
git clone https://github.com/aytekXR/yanki-mvp.git
cd yanki-mvp

# 2. Install the toolchain + dependencies + git hooks
make setup

# 3. Create your local env file and fill in the values
cp deploy/.env.example deploy/.env
#    Edit deploy/.env — set ANTHROPIC_API_KEY / OPENAI_API_KEY, or leave them
#    blank and set DRY_RUN=1 to run entirely on the mock provider ($0 spend).

# 4. Start the whole stack (Postgres + api + worker + web, hot reload)
make dev
```

Then open:

- **Frontend:** http://localhost:8140
- **Backend API health:** http://localhost:8141/healthz

Submit a URL on the landing page and watch the pipeline progress live.

> **Tip:** with `DRY_RUN=1` in `deploy/.env`, the pipeline uses a deterministic
> mock provider — no API keys required and zero API spend. Perfect for
> first-run and for the whole test suite.

---

## Make targets

`make` is the single control panel. Run `make help` (the default target) any
time to list everything.

| Target            | What it does                                                            |
| ----------------- | ----------------------------------------------------------------------- |
| `make help`       | List all targets (default goal).                                        |
| `make setup`      | Install `uv`, backend + frontend deps, and pre-commit hooks.            |
| `make bootstrap`  | Alias for `make setup`.                                                 |
| `make dev`        | Start the full dev stack (Postgres + api + worker + web, hot reload).   |
| `make test`       | Run backend (pytest) and frontend (vitest) test suites.                 |
| `make lint`       | Lint backend (ruff) and frontend (eslint).                             |
| `make fmt`        | Auto-format backend (ruff format) and frontend (prettier).             |
| `make typecheck`  | Type-check backend (mypy) and frontend (`tsc --noEmit`).               |
| `make migrate`    | Run Alembic migrations locally (`alembic upgrade head`).                |
| `make gen-types`  | Export `shared/contracts/openapi.json` + regenerate `frontend/lib/types.ts`. |
| `make e2e`        | Run the Playwright happy-path against a running stack (needs `make dev` up). |
| `make deploy`     | Build, deploy, migrate, and health-check on the server (auto-rollback). |
| `make rollback`   | Redeploy the last-good release SHA.                                     |
| `make deploy-logs`| Tail logs from the running server stack.                                |
| `make deploy-down`| Stop the server stack.                                                  |

---

## Port map

| Service        | Host port           | Notes                                                |
| -------------- | ------------------- | ---------------------------------------------------- |
| Frontend (web) | **8140**            | Next.js. Public via Caddy in prod.                   |
| Backend (api)  | **8141**            | FastAPI. `/api/*` and `/healthz` routed here.        |
| Postgres (db)  | 5432 (**dev only**) | Never published in production; internal network only.|

Host ports for `make dev` are parameterized — set `YANKI_WEB_PORT`, `YANKI_API_PORT`,
or `YANKI_DB_PORT` in `deploy/.env` to dodge conflicts with something already
running (defaults 8140 / 8141 / 5432; container-internal ports are unaffected).

In production the shared **pulse-prod Caddy** terminates TLS on
`yanki.beyondkaira.com` and path-routes `/api/*` + `/healthz` → api and
everything else → web, reaching both **over the shared docker network**
(aliases `yanki-api:8141` / `yanki-web:8140` — a containerized Caddy can't hit
host-loopback binds). The prod stack's own `127.0.0.1` binds are health-check/
debug only and parameterized (`YANKI_PROD_WEB_PORT`=8142,
`YANKI_PROD_API_PORT`=8143 — 8140 is taken by another tenant on the VPS).
Same origin, so there is no CORS.

---

## Repo mini-map — "where do I put X?"

```
yanki/
├── backend/      # Python 3.12 — FastAPI api + worker + GEO engine (one image)
│   └── app/
│       ├── api/        # HTTP layer: routes + Pydantic request/response schemas
│       ├── services/   # orchestration glue between api ⇄ db ⇄ queue
│       ├── db/         # SQLAlchemy models + query helpers
│       ├── jobs/       # Postgres job queue (FOR UPDATE SKIP LOCKED)
│       ├── pipeline/   # the GEO engine (discovery → kyc → prompts → execute → footprint → scoring)
│       ├── providers/  # LLM adapters behind one Provider interface (+ mock)
│       └── worker.py   # polls the queue, runs the pipeline
├── frontend/     # Next.js 15 + TypeScript — 3 screens (submit, progress, results)
├── shared/       # cross-language contract (contracts/openapi.json)
├── deploy/       # Docker Compose + deploy/rollback scripts (ams-pulse pattern)
├── scripts/      # repo-level dev utilities (gen_openapi.py, check_env.py)
├── .github/      # CI/CD workflows + PR template
└── docs/         # design, architecture, MVP scope, roadmap, brandkit, tests
```

**Rule of thumb:** a file's owner is the owner of the directory it lives in.
Anything under `deploy/`, `.github/`, `shared/contracts/`, or `backend/alembic/`
also needs the lead's review. See [`docs/design.md`](docs/design.md) for the full
ownership map.

**Do not hand-edit generated files** — `shared/contracts/openapi.json` and
`frontend/lib/types.ts` come from `make gen-types`. The app imports its types
from `frontend/lib/contracts.ts` instead — a hand-maintained seam that aliases
friendly names over the generated schemas and narrows the loosely-typed fields.

---

## Deploy

Deployment reuses the proven ams-pulse pattern. One command from your laptop
builds, deploys, migrates, health-checks, and auto-rolls-back on failure:

```bash
make deploy      # build + deploy + migrate + health check (auto-rollback on failure)
make rollback    # redeploy the last-good SHA if something slips through
```

**One-time prerequisites** (done once by an admin — see [`docs/architecture.md`](docs/architecture.md)):

1. On the server, create `deploy/.env` from `deploy/.env.example` and fill in real secrets.
   `make deploy` refuses to run without it and never auto-creates secrets.
2. ~~Point DNS~~ **done:** `yanki.beyondkaira.com → 161.97.172.146` resolves
   (verified 2026-07-10). Yanki serves from the **same VPS** as the other
   beyondkaira sites (pulse-prod, Ant Media, brier) — deploys must never
   disturb them.
3. Add the site block from `deploy/caddy/yanki.beyondkaira.com.caddy` to the
   shared Caddy's config (`~/repo/ams-pulse/deploy/config/Caddyfile.prod` — it
   has **no import dir**), then `caddy validate` and **reload** (never restart)
   inside `pulse-prod-caddy-1`.

Compose project name is `yanki-prod`. Yanki runs **no** Caddy of its own: web +
api join the shared Caddy's network (`pulse-prod_default`) as `yanki-web` /
`yanki-api`, and the only host binds are loopback health-check ports
(8142/8143 by default). The pulse-prod stack must be up first (its network is
`external` to Yanki's compose).

---

## Documentation

| Doc                                                     | Audience              | What's in it                                             |
| ------------------------------------------------------- | --------------------- | ------------------------------------------------------- |
| [docs/design.md](docs/design.md)                        | Whole team            | Repo structure, folder rationale, ownership, ADR log.   |
| [docs/architecture.md](docs/architecture.md)            | Engineers / on-call   | System + data-flow diagrams, job lifecycle, deploy topology. |
| [docs/02-mvp.md](docs/02-mvp.md)                        | PM / QA / founders    | MVP PRD: scope, users, flow, acceptance criteria, out-of-scope. |
| [docs/roadmap.md](docs/roadmap.md)                      | Leadership / engineers| Phased path from MVP to the Semrush alternative.        |
| [docs/frontend-brandkit.md](docs/frontend-brandkit.md)  | Frontend              | Colors, type, spacing, components, voice/tone (EN + TR).|
| [docs/test-suite.md](docs/test-suite.md)                | Every engineer        | Test pyramid, TDD workflow, fixtures, coverage targets. |

See also [CONTRIBUTING.md](CONTRIBUTING.md) for the branch/PR/commit flow and
[SECURITY.md](SECURITY.md) for the secret policy and how to report issues.
