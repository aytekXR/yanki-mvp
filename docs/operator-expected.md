# Operator Expected — everything only a human can do

*The single operator file (the former `operator-actions.md` was merged in
here, 2026-07-10). Maintained by the orchestrator at every session close.
Tick items as you do them; the next session re-checks `deploy/.env`, the git
remote, and CI status at start regardless. Nothing here blocks local
development — `make dev` + `make test` work with zero keys and zero cost
(DRY_RUN).*

Last updated: 2026-07-10 (session 8 close: **your three directives are
done** — (1) prod is **LIVE-PROVIDERS** (`DRY_RUN=0`, redeployed, verified:
a real analysis ran through https://yanki.beyondkaira.com with 10 Claude +
10 gpt-5-nano responses, real KYC for anthropic.com); (2) **KYC now renders
as a proper profile card** on the result page (was a raw JSON dump) —
see it live:
https://yanki.beyondkaira.com/analyses/17164747-a6a7-40ab-bc3b-d4d4d6e9ee62 ;
(3) the **OpenAI cost leg is recorded**: $0.0026/analysis → **measured
full-panel cost $0.0162/analysis ≈ 1% of the $49 plan**. Your Caddyfile
commit in ams-pulse (d538631) is confirmed. **One thing is now genuinely
urgent and only you can do part of it: item 1 below.**)

## Do now

- [ ] **1. Set hard spend caps in both provider consoles.** Prod now runs
  real keys on a public URL **with no rate limiting yet** (you accepted this
  by going live; the code-side fix is P5.0, the first task of the next
  session — until it lands, anyone who finds the URL can trigger
  ~$0.0162-per-analysis spend without bound). Only you can cap the blast
  radius today:
  - **Anthropic:** console.anthropic.com → Billing/Limits → set a monthly
    spend limit (e.g. $10).
  - **OpenAI:** platform.openai.com → Billing → usage limits (e.g. $10/mo).
  - Escape hatch any time: set `DRY_RUN=1` in `deploy/.env`, then
    `sg docker -c "make deploy"` → back to $0 mock mode.
- [ ] **2. Eyeball the KYC card + live result** (2 minutes, no tooling):
  open the link in the header above — you should see the score gauge, then
  a "Company profile (KYC)" card (company name large, description,
  industry/locations rows, chip lists for products/competitors/etc.), then
  prompts and the response table. Say if you want the card's content or
  order changed — KYC being "very important" was implemented as
  *prominent card directly under the score*.

## Done (this session and before)

- [x] **3. Run-mode decision → LIVE.** Flipped + redeployed 2026-07-10
  (session 8), on your directive.
- [x] **4. OpenAI billing.** Quota works; `gpt-5-nano` leg proven live on
  prod ($0.0026/analysis).
- [x] **5. Caddyfile committed in ams-pulse** (`d538631`) — verified clean
  working tree there.
- [x] **6. First deploy (P4.2)** — session 7; deploy + rollback exercised,
  co-tenants undisturbed, TLS live.
- [x] **7. Real API keys → P4.1** — session 6; now fully closed by the
  session-8 OpenAI leg.
- [x] **8. GitHub + CI** — `aytekXR/yanki-mvp`, 5/5 jobs green since
  session 4.
- [x] **9. DNS** — `yanki.beyondkaira.com → 161.97.172.146`.
- [x] **10. `POSTGRES_PASSWORD`** — real 32-char value generated into
  `deploy/.env` (session 7); copy to a password manager if you keep one.

## Optional

- [ ] **11. Local browser e2e needs root once** (fully skippable — CI proves
  the browser e2e on every push):
  ```bash
  cd frontend && sudo npx playwright install-deps chromium
  ```

## Later — Phase 5, the public checker (in build; these come due at P5.7/P5.11)

- [ ] **12. Two more API keys** when P5.7/P5.11 come up: `GEMINI_API_KEY` +
  `PERPLEXITY_API_KEY`, plus a grounding/ToS sanity check for both.
- [ ] **13. Checker product decisions** (needed before the checker goes live):
  - **Turkish sign-off owner.** Native Turkish prompts + UI copy need a
    native-speaker sign-off before the loud launch; no sign-off → EN-only
    launch ("no Turkish beats bad Turkish") — who is the named decider?
  - **Abuse thresholds.** Defaults are guesses: 5 checks/IP/hour, 3 fresh
    runs/brand/day, $50/day cost cap. Confirm free-tier generosity vs spend.
  - **Email-gate strength.** A single unverified email is assumed (max lead
    capture). Add verification / disposable-domain blocking / captcha, or not?
  - **The one free raw answer.** Default: first answer that mentions the brand.

## Later — design (non-blocking)

- [ ] **14. Brandkit v2 adoption decision.** You dropped `brandkit/` into the
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
