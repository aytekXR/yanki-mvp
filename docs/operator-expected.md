# Operator Expected — everything only a human can do

*The single operator file (the former `operator-actions.md` was merged in
here, 2026-07-10). Maintained by the orchestrator at every session close.
Tick items as you do them; the next session re-checks `deploy/.env`, the git
remote, and CI status at start regardless. Nothing here blocks local
development — `make dev` + `make test` work today with zero keys and zero
cost (DRY_RUN).*

Last updated: 2026-07-10 (session 7 close: **P4.2 done — the deploy you
asked for happened. https://yanki.beyondkaira.com is LIVE**, TLS by the
shared Caddy, all four co-tenant sites verified undisturbed before and
after (pulse 200 / apex 200 / www 301 / ams 200), `make rollback`
exercised, a mock analysis ran end-to-end on prod. **The MVP plan is
32/32 = 100%.** The session did items 4/6/7 for you under your "let's
deploy" directive — including generating a real `POSTGRES_PASSWORD` —
so what's left for you is below: **two decisions (items 1–2) and one
30-second commit in your ams-pulse repo (item 3). Nothing blocks the
next session** — it can start Phase 5 (P5.1) as is.)

## Do now — decisions only you can make

- [ ] **1. Decide: keep prod in mock mode, or go live-providers?** Prod
  deliberately runs **`DRY_RUN=1`** (every analysis uses the $0 deterministic
  mock — the deploy machinery, DB, worker, UI are all real). Reason: there is
  **no rate limiting yet** (tech-debt #2, planned P5.6), so a public URL with
  real keys is unmetered spend — anyone who finds the URL can trigger paid
  LLM calls (measured $0.0132/analysis on the Anthropic leg; tiny per call,
  unbounded in volume). When you want the live pipeline on prod (e.g. for a
  design-partner demo):
  ```bash
  # in ~/repo/yanki-mvp: set DRY_RUN=0 in deploy/.env, then
  sg docker -c "make deploy"        # or: cd deploy && sg docker -c "docker compose -p yanki-prod -f docker-compose.prod.yml up -d"
  ```
  Recommendation: flip it for supervised demos, flip back after — or wait for
  P5.6 (rate limits + kill switch + daily cost cap).
- [ ] **2. OpenAI billing (was 1b) — your OpenAI key still has no usable
  quota.** Every call returned `429 insufficient_quota` (billing, not rate
  limiting): add credits / enable billing for that key's org at
  platform.openai.com → Billing. The provider is already on the cheapest
  model (`gpt-5-nano`, $0.05/$0.40 per MTok); once quota exists, the next
  session runs one cheap re-run (~$0.02) to record the OpenAI cost leg.
  Until then the panel runs live-Anthropic + stubs (when DRY_RUN=0).
- [ ] **3. Commit the Caddyfile edit in YOUR ams-pulse repo.** Publishing
  yanki appended a site block to
  `~/repo/ams-pulse/deploy/config/Caddyfile.prod` (that repo now shows
  `M deploy/config/Caddyfile.prod`, +35 lines, nothing else touched). It is
  **live and working** — but uncommitted in a repo this project doesn't own.
  Commit it there so a future ams-pulse deploy doesn't clobber yanki's
  routing. Heads-up for any future edit: never append the yanki block twice
  (duplicate site key fails validation), and always
  `docker exec pulse-prod-caddy-1 caddy validate --config /etc/caddy/Caddyfile`
  before `caddy reload` — **never restart** that container.

## FYI — done for you this session (nothing to do, just know it)

- [x] **4. `POSTGRES_PASSWORD` is now real.** The `change-me-in-prod`
  placeholder in `deploy/.env` was replaced with a generated 32-char random
  value before the first deploy (the prod DB volume was created fresh with
  it). It lives only in the gitignored `deploy/.env` — copy it into your
  password manager if you keep one. Also added there: explicit
  `YANKI_PROD_WEB_PORT=8142` / `YANKI_PROD_API_PORT=8143` (previously
  implicit defaults).
- [x] **5. Shared-Caddy edit + reload (was item 6)** — done under your
  "let's deploy" directive, validate-before-reload, co-tenants spot-checked
  around it (see item 3 for the one follow-up: committing it).
- [x] **6. First `make deploy` (was item 7)** — done, twice: the first run
  caught a real bug (prod web image build omitted devDependencies →
  `next build` failed; fixed in commit 3a84943), the second deployed clean.
  `make rollback` also exercised. Old tech-debt #1 repaid.

## Done earlier

- [x] **7. Real API keys → P4.1 (cost validation).** ✅ 2026-07-10, session 6:
  one real analysis end-to-end in ~40s, measured panel cost
  **$0.0132/analysis** ≈ 1% of the $49 plan (bar: <35%).
- [x] **8. Push to GitHub → CI.** ✅ `aytekXR/yanki-mvp`, all five jobs green
  since session 4 (backend / frontend / contract / secrets / e2e).
- [x] **9. DNS A record:** `yanki.beyondkaira.com → 161.97.172.146` ✅.

## Optional

- [ ] **10. Local browser e2e needs root once** (fully skippable — CI proves
  the browser e2e on every push):
  ```bash
  cd frontend && sudo npx playwright install-deps chromium
  ```

## Later — Phase 5, the public checker (build gate is now OPEN)

The MVP is deployed, so Phase 5 (P5.1–P5.11) can start next session. These
sit with you but block nothing until the tasks that need them come up:

- [ ] **11. Two more API keys** when P5.7/P5.11 come up: `GEMINI_API_KEY` +
  `PERPLEXITY_API_KEY`, plus a grounding/ToS sanity check for both.
- [ ] **12. Checker product decisions** (needed before the checker goes live):
  - **Turkish sign-off owner.** Native Turkish prompts + UI copy need a
    native-speaker sign-off before the loud launch; no sign-off → EN-only
    launch ("no Turkish beats bad Turkish") — who is the named decider?
  - **Abuse thresholds.** Defaults are guesses: 5 checks/IP/hour, 3 fresh
    runs/brand/day, $50/day cost cap. Confirm free-tier generosity vs spend.
  - **Email-gate strength.** A single unverified email is assumed (max lead
    capture). Add verification / disposable-domain blocking / captcha, or not?
  - **The one free raw answer.** Default: first answer that mentions the brand.

## Later — design (non-blocking)

- [ ] **13. Brandkit v2 adoption decision.** You dropped `brandkit/` into the
  repo on 2026-07-10 and chose to **skip integrating it for now** — nothing
  happens until you say so. When you want it adopted, decide: does v2
  supersede `docs/frontend-brandkit.md` (v1) and should the frontend tokens
  change to match? (Heads-up from tech-debt #13: a palette change means
  re-computing the WCAG contrast ratios by hand — axe can't check contrast
  under jsdom.)

## Local-machine quirks (informational)

- **Ports 5432 and 8140 are already taken on this host.** The dev stack is
  parameterized; put overrides in `deploy/.env` (or prefix the command):
  ```bash
  YANKI_DB_PORT=5434 YANKI_WEB_PORT=8240 make dev
  # web → http://localhost:8240 , api stays on 8141
  ```
  The **prod** stack's loopback binds are 8142/8143 (health checks only —
  the shared Caddy reaches the containers via network aliases).
- **Node is v20 here; README recommends 22 LTS.** Everything builds and tests
  green on 20 — upgrade is optional.
- **Docker group membership may not apply to long-lived sessions.** `aytek`
  is in the `docker` group but processes started before the membership was
  granted get "permission denied" on the socket. Fix: a fresh login shell, or
  prefix commands with `sg docker -c "…"`.
