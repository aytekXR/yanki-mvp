# Operator Actions — things only a human can do

*Maintained by the orchestrator. Check this file at the start of every session.
Nothing here blocks local development — `make dev` + `make test` work today with
zero keys and zero cost (DRY_RUN). Items are ordered by when you'll want them.*

Last updated: 2026-07-09 (session 2).

## ⚡ Expected from you right now (session-2 status)

Session 2 is **complete**. It found **no keys in `deploy/.env` and no GitHub
remote**, so P4.1 (real-key smoke test) was skipped and the session did the
key-free tasks instead: P4.3 (CI hardening + gitleaks) done, P4.4 (e2e-in-CI)
authored, P4.5 (accessibility audit) done — all local gates (lint / typecheck /
test / contract-drift) and a live DRY_RUN smoke test are green. To unblock the
rest of Phase 4, the two items below are what's needed from you — everything
else can wait:

1. **Provide real API keys, then decide `DRY_RUN=0` (unblocks P4.1 → P4.2).**
   Put real `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` into `deploy/.env`. See
   item 1 below for the cost-read exercise.
2. **Push the repo to GitHub (proves CI).** There are now **five** CI jobs
   (backend / frontend / contract-drift / secrets-gitleaks / e2e-playwright).
   **None has ever executed on GitHub.** The first four were validated
   locally; the **e2e job has never run anywhere** (Chromium cannot launch on
   this host without root system libraries). On first push, verify all five go
   green. See item 2 below.
3. *(Optional)* Install Playwright's system libraries locally
   (`sudo npx playwright install-deps chromium`) if you want to run the e2e
   suite on this machine. See item 3 below.
4. *(At P4.2 time)* server `.env`, DNS, Caddy snippet, supervised first
   deploy. See items 4+ below.

## Blocking nothing today, needed before/at launch

1. **Real-API smoke test + cost read (Week-1 finance exercise, NFR-1).**
   Spends real money, so it is your call. Put real `ANTHROPIC_API_KEY` /
   `OPENAI_API_KEY` into `deploy/.env`, set `DRY_RUN=0`, run one analysis
   against a real site, then read the two provider dashboards and compare cost
   per analysis against the plan margins in `docs/00-first-mvp-draft.md`.
   ```bash
   cp deploy/.env.example deploy/.env   # then edit keys + DRY_RUN=0
   make dev                             # submit a URL at the web port
   ```

2. **Push to GitHub (publishing decision).** No remote is configured, so CI
   (`.github/workflows/ci.yml`) has never executed. README assumes
   `github.com/Beyond-Kaira/yanki`. Once pushed, check that all **five** CI
   jobs go green on the first run:
   - **backend** — ruff + mypy + pytest (Postgres service).
   - **frontend** — typecheck + lint + vitest + build.
   - **contract** — OpenAPI + generated-types drift gate.
   - **secrets** — gitleaks full-history secret scan.
   - **e2e** — Playwright happy path against the DRY_RUN docker stack (this
     one has never run anywhere yet — see item 3).

3. **Playwright e2e on this machine needs root once (optional).** The e2e CI
   job now exists (P4.4 authored — `frontend/e2e/happy-path.spec.ts`), so after
   the push in item 2 the browser e2e runs in CI and you need nothing locally.
   If you *do* want to run it on this host, Chromium downloads fine but won't
   launch without system libraries, and installing them needs sudo:
   ```bash
   cd frontend && sudo npx playwright install-deps chromium
   ```
   Until either path runs, the happy path is verified by API-level e2e and a
   live DRY_RUN smoke test (both done, green).

## Needed at first server deploy (Phase 4)

4. **One-time server prerequisites** (from README §Deploy):
   - Create `deploy/.env` on the server from `.env.example` with real secrets
     (`make deploy` refuses to run without it; `POSTGRES_PASSWORD` must be set).
   - DNS A record: `test.beyondkaira.com → 161.97.172.146`.
   - Drop `deploy/caddy/test.beyondkaira.com.caddy` into the shared pulse-prod
     Caddy import dir, `caddy validate`, then reload (never restart) Caddy.
   - **Supervise the first `make deploy`** — `deploy/deploy.sh` and
     `rollback.sh` are written but have never run against a real server
     (tracked in tech debt).

## Local-machine quirks (informational)

5. **Ports 5432 and 8140 are already taken on this host.** The dev stack is
   parameterized; put overrides in `deploy/.env` (or prefix the command):
   ```bash
   YANKI_DB_PORT=5434 YANKI_WEB_PORT=8240 make dev
   # web → http://localhost:8240 , api stays on 8141
   ```

6. **Node is v20 here; README recommends 22 LTS.** Everything builds and tests
   green on 20 — upgrade is optional.

7. **Docker group membership may not apply to long-lived sessions.** `aytek`
   is in the `docker` group (per `/etc/group`) but processes started before
   the membership was granted get "permission denied" on the socket. Fix: use
   a fresh login shell, or prefix commands with `sg docker -c "…"`.
