# Operator Expected — everything only a human can do

*The single operator file (the former `operator-actions.md` was merged in
here, 2026-07-10). Maintained by the orchestrator at every session close.
Tick items as you do them; the next session re-checks `deploy/.env`, the git
remote, and CI status at start regardless. Nothing here blocks local
development — `make dev` + `make test` work today with zero keys and zero
cost (DRY_RUN).*

Last updated: 2026-07-10 (session 6 close: **keys added → first LIVE run
succeeded — P4.1 done**. Real KYC + score for anthropic.com in ~40s;
measured cost **$0.0132/analysis** on the Anthropic leg ≈ 1% of the $49
plan — the NFR-1 margin holds with ~35× headroom. Providers now on the
cheapest models per your directive: Claude Haiku 4.5 (already was) +
`gpt-5-nano` (switched from gpt-4o-mini, 3× cheaper input). One finding
needs you: **your OpenAI key has no usable quota** — see item 1b.)

**Session-5 result: the final key-free task landed** — the frontend lint
script migrated off the deprecated `next lint` to the ESLint CLI (old
tech-debt #10; the future Next 16 bump is no longer lint-blocked), verified
locally against every CI frontend step and green on the real runner. CI
remains 5/5 green. **Where we stand:** MVP plan (Phases 0–4) ≈ 94%
(30 of 32 tasks; counting the 11 frozen Phase-5 tasks, 30/43 ≈ 70%);
production readiness ≈ 75% — the missing ~25% is entirely the outside-world
proof only you can trigger. **There is now NO session work left that doesn't
need you first:** real keys (item 1), then the supervised first deploy
(items 4–7). A session started with no keys can only verify and close.

## Do now

- [x] **1. Real API keys → P4.1 (cost validation).** ✅ Done (2026-07-10,
  session 6): you added the keys, the agent ran one real analysis
  (`https://www.anthropic.com`) end-to-end in ~40s — correct KYC profile,
  `geo_score=0.2`, **measured panel cost $0.0132/analysis** (10 × Claude
  Haiku 4.5, ~$0.0013/response, from the `cost_usd` columns). Margin vs
  [00-first-mvp-draft.md](00-first-mvp-draft.md): daily full-panel ≈
  $0.45/mo/customer ≈ **1% of the $49 plan** (bar: <35%). Optional
  cross-check: your Anthropic console should show ~13 Haiku calls / ~$0.02
  total for 2026-07-10.
- [ ] **1b. NEW — your OpenAI key has no usable quota.** Every call returned
  `429 insufficient_quota` ("check your plan and billing details") — that's
  billing, not rate limiting: add credits / enable billing for that key's
  org at platform.openai.com → Billing. The provider is already switched to
  the cheapest model (`gpt-5-nano`, $0.05/$0.40 per MTok); once quota
  exists, the next session runs one cheap re-run (~$0.02) to record the
  OpenAI cost leg. Until then the panel runs live-Anthropic + stubs.

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

## Do next — the first deploy (P4.2 — the LAST MVP task, now unblocked)

*Retargeted 2026-07-10 at your direction: Yanki serves from **this VPS** at
**`yanki.beyondkaira.com`**, co-tenant with the live sites (pulse-prod, Ant
Media, brier) — deploys must never disturb them. The deploy configs were
updated to match the real topology (shared-Caddy network aliases; loopback
ports 8142/8143 because 8140/5432 are taken here).*

- [ ] **4. Server `deploy/.env`** — this VPS **is** the server, so the existing
  `deploy/.env` is it: fill in the real secrets (same file as item 1) and
  **replace the placeholder `POSTGRES_PASSWORD`** (it currently holds the
  change-me example value — fine for dev, not for a prod stack); optionally
  override `YANKI_PROD_WEB_PORT`/`YANKI_PROD_API_PORT` (defaults 8142/8143
  are free today).
- [x] **5. DNS A record:** ~~point it~~ **done** — `yanki.beyondkaira.com →
  161.97.172.146` verified resolving (2026-07-10).
- [ ] **6. Shared-Caddy edit (in the ams-pulse repo, so it's yours):** add the
  site block from `deploy/caddy/yanki.beyondkaira.com.caddy` to
  `~/repo/ams-pulse/deploy/config/Caddyfile.prod` (the shared Caddy mounts that
  one file read-only — it has **no import dir**), then:
  ```bash
  docker exec pulse-prod-caddy-1 caddy validate --config /etc/caddy/Caddyfile
  docker exec pulse-prod-caddy-1 caddy reload   --config /etc/caddy/Caddyfile
  ```
  **Reload, never restart** — the other live sites terminate TLS on it. After
  the reload, spot-check that pulse + ams.* still serve.
- [ ] **7. Supervise the first `make deploy`** — `deploy/deploy.sh` and
  `rollback.sh` are written to the ams-pulse pattern and reviewed, but have
  never run against a real server (tech-debt #1). Note: the pulse-prod stack
  must be up first (Yanki's prod compose joins its network as `external:`),
  and P4.2's acceptance now includes the co-tenant check — every pre-existing
  site still serves before and after.

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

## Later — design (non-blocking)

- [ ] **10. Brandkit v2 adoption decision.** You dropped `brandkit/` (the
  Yankı brand v2 package: petrol-ink/echo-teal palette, logos, icons,
  `frontend-brandkit-v2.md`, design rationale) into the repo on 2026-07-10
  and chose to **skip integrating it for now** — so nothing happens until
  you say so. When you want it adopted, decide: does v2 supersede
  `docs/frontend-brandkit.md` (v1) and should the frontend tokens change to
  match? (Heads-up from tech-debt #14: a palette change means re-computing
  the WCAG contrast ratios by hand — axe can't check contrast under jsdom.)

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
