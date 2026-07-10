# Operator Actions — things only a human can do

*Maintained by the orchestrator. Check this file at the start of every session.
Nothing here blocks local development — `make dev` + `make test` work today with
zero keys and zero cost (DRY_RUN). Items are ordered by when you'll want them.
For the tick-list-only version, see
[operator-expected.md](operator-expected.md).*

Last updated: 2026-07-10 (session 4 close).

## ⚡ Expected from you right now (session-4 status)

Session 4 is **complete** and it closed the CI story: **all five CI jobs are
green** on `github.com/aytekXR/yanki-mvp`. The red e2e job was fixed by
reordering its steps (`npm ci` + Playwright install now run *before* the
bind-mounting compose stack boots — dockerd was creating
`frontend/node_modules` on the host as root, breaking the later install; the
mechanism was reproduced and the fix verified locally before pushing). Run
29059944092 went 5/5 green and **the Playwright happy path executed for the
first time anywhere: `1 passed (6.6s)`** — P4.4 is done. A second push bumped
the Node-20-deprecated CI actions (checkout v7 / setup-node v6 / setup-uv v7)
and run 29060093072 stayed 5/5 green with the deprecation warnings cleared.
Tech-debt items 2–3 repaid (the list was renumbered — see
[tech-debt.md](tech-debt.md)'s header for the old→new map).

**Where we stand:** MVP plan (Phases 0–4) ≈ 94% (30 of 32 tasks; counting the
11 frozen Phase-5 tasks, 30/43 ≈ 70% of the enlarged plan — full snapshot in
[implementation-plan.md](implementation-plan.md) §Readiness snapshot);
production readiness ≈ 75%. The missing ~25% is entirely the outside-world
proof only you can trigger. The session is closed and the next-session brief
is ready in [sessions/2026-07-10-02.md](sessions/2026-07-10-02.md) §6.
**Item 1 below is the only thing gating everything:**

1. **Provide real API keys, then decide `DRY_RUN=0` (unblocks P4.1 → P4.2).**
   Put real `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` into `deploy/.env`. See
   item 1 below for the cost-read exercise.
2. *(At P4.2 time, after item 1)* server `.env`, DNS, Caddy snippet,
   supervised first deploy. See items 4+ below.
3. *(Nothing else.)* Browser e2e is now proven in CI on every push, so the
   local-sudo Playwright install (item 3 below) is fully optional.

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

2. **Push to GitHub — ✅ done (2026-07-10), and CI is now fully green
   (session 4).** `main` is on `github.com/aytekXR/yanki-mvp` (README clone
   URL updated from the assumed `Beyond-Kaira/yanki`). Latest results (runs
   29059944092 + 29060093072):
   - **backend** — ruff + mypy + pytest (Postgres service): ✅ green.
   - **frontend** — typecheck + lint + vitest + build: ✅ green.
   - **contract** — OpenAPI + generated-types drift gate: ✅ green.
   - **secrets** — gitleaks full-history scan (binary download path proven): ✅ green.
   - **e2e** — ✅ green since session 4's install-order fix; the Playwright
     happy path ran for the first time anywhere and passed (`1 passed, 6.6s`).
     One accepted dependency: the pipeline's discovery step really fetches
     `example.com` even under DRY_RUN, so this job needs runner egress — a
     red e2e *after* green health waits is likelier a network flake than an
     app bug (tech-debt #9).

3. **Playwright e2e on this machine needs root once (fully optional).** CI
   now proves the browser e2e on every push, so you need nothing locally.
   If you *do* want to run it on this host, Chromium downloads fine but won't
   launch without system libraries, and installing them needs sudo:
   ```bash
   cd frontend && sudo npx playwright install-deps chromium
   ```

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
