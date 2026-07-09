# Operator Actions — things only a human can do

*Maintained by the orchestrator. Check this file at the start of every session.
Nothing here blocks local development — `make dev` + `make test` work today with
zero keys and zero cost (DRY_RUN). Items are ordered by when you'll want them.*

Last updated: 2026-07-09 (session 1).

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
   `github.com/Beyond-Kaira/yanki`. Once pushed, check that all three CI jobs
   (backend / frontend / contract-drift) go green on the first run.

3. **Playwright e2e on this machine needs root once.** Chromium downloads fine
   but won't launch without system libraries; installing them needs sudo:
   ```bash
   cd frontend && sudo npx playwright install-deps chromium
   ```
   Alternative: skip locally — the e2e job can run in CI after item 2.
   Until then the happy path is verified by API-level e2e (done, green).

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
