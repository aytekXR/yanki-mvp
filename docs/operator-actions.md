# Operator Actions — things only a human can do

*Maintained by the orchestrator. Check this file at the start of every session.
Nothing here blocks local development — `make dev` + `make test` work today with
zero keys and zero cost (DRY_RUN). Items are ordered by when you'll want them.
For the tick-list-only version, see
[operator-expected.md](operator-expected.md).*

Last updated: 2026-07-10 (session 3).

## ⚡ Expected from you right now (session-3 status)

Session 3 is **complete**. It re-checked both gates and found **still no keys
in `deploy/.env` and still no GitHub remote**, so per the session-2 brief it
executed the last key-free task: **P4.6 — the roadmap-"Next" free public
checker is now decomposed into 11 session-sized Phase-5 tasks** (P5.1–P5.11 in
[implementation-plan.md](implementation-plan.md), with its build gate, lanes,
and merge risks). Planning only — no code changed; `make test` stayed green
(64 backend + 20 frontend tests).

**Where we stand:** MVP plan (Phases 0–4) ≈ 92% (29.5 of 32 tasks; counting the
11 frozen Phase-5 tasks, 29.5/43 ≈ 69% of the enlarged plan — full snapshot in
[implementation-plan.md](implementation-plan.md) §Readiness snapshot);
production readiness ≈ 70%, **unchanged** — the missing ~30% is entirely the
outside-world proof only you can trigger. The session is closed and the
next-session brief is ready in
[sessions/2026-07-10-01.md](sessions/2026-07-10-01.md) §6 (+ the §9 CI
addendum). **Post-close update: you did item 2** — the push landed on
`github.com/aytekXR/yanki-mvp` and the first CI run went **4/5 green**
(backend / frontend / contract / secrets); the e2e job failed on a CI-job
ownership/order bug (diagnosed in tech-debt item 2 — the agent fixes it next
session, nothing needed from you). Item 1 below is now the only thing gating:

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

2. **Push to GitHub — ✅ done (2026-07-10).** `main` is on
   `github.com/aytekXR/yanki-mvp` (README clone URL updated from the assumed
   `Beyond-Kaira/yanki`). First-run results (run 29058049101):
   - **backend** — ruff + mypy + pytest (Postgres service): ✅ green.
   - **frontend** — typecheck + lint + vitest + build: ✅ green.
   - **contract** — OpenAPI + generated-types drift gate: ✅ green.
   - **secrets** — gitleaks full-history scan (binary download path proven): ✅ green.
   - **e2e** — ❌ red at `npm ci`: the job boots the bind-mounting compose
     stack first and the root container owns `frontend/node_modules` before
     the runner installs. Agent-side fix, next session's first task
     (tech-debt item 2); the Playwright spec itself still hasn't run.

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

## Phase-5 decisions wanted (non-blocking today; needed before the checker goes live)

Session 3 decomposed the free public checker (Phase 5). Building it stays
frozen until the MVP is signed off (items 1–2 above + first deploy), but four
product decisions and two future keys sit with you — full detail in the
"Phase-5 open questions" block of
[implementation-plan.md](implementation-plan.md):

- **Turkish sign-off owner.** Native Turkish prompts + UI copy need a
  native-speaker sign-off before the loud launch. Who signs off — and who is
  the named operator authorized to invoke the EN-only fallback ("no Turkish
  beats bad Turkish")?
- **Abuse thresholds.** Defaults are guesses: 5 checks/IP/hour, 3 fresh
  runs/brand/day, $50/day cost cap. Confirm the free-tier generosity vs spend.
- **Email-gate strength.** A single unverified email is assumed (max lead
  capture). Add verification / disposable-domain blocking / captcha before
  go-live, or not?
- **The one free raw answer.** Default: first answer that mentions the brand.
- **Two more API keys later** (P5.7/P5.11): `GEMINI_API_KEY` +
  `PERPLEXITY_API_KEY`, plus a grounding/ToS check for both — not needed now.

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
