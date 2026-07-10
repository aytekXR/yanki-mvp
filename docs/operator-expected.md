# Operator Expected — everything only a human can do

*The single operator file (the former `operator-actions.md` was merged in
here, 2026-07-10). Maintained by the orchestrator at every session close.
Tick items as you do them; the next session re-checks `deploy/.env`, the git
remote, and CI status at start regardless. Nothing here blocks local
development — `make dev` + `make test` work today with zero keys and zero
cost (DRY_RUN).*

Last updated: 2026-07-10 (session 4 post-close: operator files merged;
**CI is fully green: 5/5 jobs**).

**Session-4 result: the e2e job is fixed and ALL FIVE CI jobs are green**
(runs 29059944092 + 29060093072) — the Playwright happy path executed for the
first time anywhere and passed (`1 passed, 6.6s`), and the deprecated-action
annotations are cleared. **Where we stand:** MVP plan (Phases 0–4) ≈ 94%
(30 of 32 tasks; counting the 11 frozen Phase-5 tasks, 30/43 ≈ 70%);
production readiness ≈ 75% — the missing ~25% is entirely the outside-world
proof only you can trigger. The MVP build is done except for the two things
only you can unblock: real keys (item 1), then the supervised first deploy
(items 4–7).

## Do now — the one thing everything else waits on

- [ ] **1. Real API keys → unblocks P4.1 (cost validation), then P4.2 (deploy).**
  This is the Week-1 finance exercise (NFR-1) and it spends real money, so
  timing is your call. Until then, sessions have only one small hygiene
  fallback left (ESLint CLI migration, debt #10).
  ```bash
  cp deploy/.env.example deploy/.env
  # then edit: ANTHROPIC_API_KEY=…, OPENAI_API_KEY=…, DRY_RUN=0
  make dev        # submit one real URL at the web port
  ```
  The agent then records measured cost per analysis (the `cost_usd` columns);
  you read the two provider dashboards and compare cost per analysis against
  the plan margins in [00-first-mvp-draft.md](00-first-mvp-draft.md).

## Done

- [x] **2. Push to GitHub → first-ever CI run.** ✅ Done (2026-07-10,
  `aytekXR/yanki-mvp`; README clone URL updated from the assumed
  `Beyond-Kaira/yanki`) — and as of session 4 **all five jobs are green**:
  - **backend** — ruff + mypy + pytest (Postgres service): ✅
  - **frontend** — typecheck + lint + vitest + build: ✅
  - **contract** — OpenAPI + generated-types drift gate: ✅
  - **secrets** — gitleaks full-history scan (binary download path proven): ✅
  - **e2e** — ✅ green since session 4's install-order fix; the Playwright
    happy path ran for the first time anywhere and passed. One accepted
    dependency: the pipeline's discovery step really fetches `example.com`
    even under DRY_RUN, so this job needs runner egress — a red e2e *after*
    green health waits is likelier a network flake than an app bug
    (tech-debt #9).

## Optional

- [ ] **3. Local browser e2e needs root once** (fully skippable — CI now
  proves the browser e2e on every push). Chromium downloads fine on this
  host but won't launch without system libraries, and installing them needs
  sudo:
  ```bash
  cd frontend && sudo npx playwright install-deps chromium
  ```

## Later — at first deploy (P4.2, after item 1)

- [ ] **4. Server `deploy/.env`** created on the server from `.env.example`
  with real secrets — `make deploy` refuses to run without it, and
  `POSTGRES_PASSWORD` must be set.
- [ ] **5. DNS A record:** `test.beyondkaira.com → 161.97.172.146`.
- [ ] **6. Caddy import:** drop `deploy/caddy/test.beyondkaira.com.caddy` into
  the shared pulse-prod import dir, `caddy validate`, then **reload** (never
  restart).
- [ ] **7. Supervise the first `make deploy`** — `deploy/deploy.sh` and
  `rollback.sh` are written to the ams-pulse pattern and reviewed, but have
  never run against a real server (tech-debt #1).

## Later — Phase 5, the public checker (only after the MVP is signed off)

Building the free public checker stays frozen until the MVP is signed off
(item 1 + first deploy); these sit with you but block nothing today. Full
detail: the "Phase-5 open questions" block in
[implementation-plan.md](implementation-plan.md).

- [ ] **8. Two more API keys** when P5.7/P5.11 come up: `GEMINI_API_KEY` +
  `PERPLEXITY_API_KEY`, plus a grounding/ToS sanity check for both.
- [ ] **9. Checker product decisions** (needed before the checker goes live):
  - **Turkish sign-off owner.** Native Turkish prompts + UI copy need a
    native-speaker sign-off before the loud launch; no sign-off → EN-only
    launch ("no Turkish beats bad Turkish") — who is the named decider?
  - **Abuse thresholds.** Defaults are guesses: 5 checks/IP/hour, 3 fresh
    runs/brand/day, $50/day cost cap. Confirm free-tier generosity vs spend.
  - **Email-gate strength.** A single unverified email is assumed (max lead
    capture). Add verification / disposable-domain blocking / captcha, or not?
  - **The one free raw answer.** Default: first answer that mentions the brand.

## Local-machine quirks (informational)

- **Ports 5432 and 8140 are already taken on this host.** The dev stack is
  parameterized; put overrides in `deploy/.env` (or prefix the command):
  ```bash
  YANKI_DB_PORT=5434 YANKI_WEB_PORT=8240 make dev
  # web → http://localhost:8240 , api stays on 8141
  ```
- **Node is v20 here; README recommends 22 LTS.** Everything builds and tests
  green on 20 — upgrade is optional.
- **Docker group membership may not apply to long-lived sessions.** `aytek`
  is in the `docker` group but processes started before the membership was
  granted get "permission denied" on the socket. Fix: a fresh login shell, or
  prefix commands with `sg docker -c "…"`.
