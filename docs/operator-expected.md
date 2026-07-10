# Operator Expected — everything only a human can do

*The single operator file (the former `operator-actions.md` was merged in
here, 2026-07-10). Maintained by the orchestrator at every session close.
Tick items as you do them; the next session re-checks `deploy/.env`, the git
remote, and CI status at start regardless. Nothing here blocks local
development — `make dev` + `make test` work with zero keys and zero cost
(DRY_RUN).*

Last updated: 2026-07-10 (session 9 close: **nothing is urgent anymore, and
nothing blocks the next session (P5.2).** The rate-limit hole you accepted
when going live is CLOSED — **P5.0 is deployed and verified on prod**: the
6th submit per IP per hour gets a 429, a global 100/day cap bounds
worst-case abuse at **≈$1.62/day**, and setting either limit to 0 in
`deploy/.env` is an instant kill-switch. **P5.1 also shipped**: the checker
API (`POST /api/v1/checker` + lead capture + 24h per-brand reuse) is live
but inert — checker runs stay queued at $0 until P5.2 wires the pipeline.
Total live spend to date: **$0.056** (session-8 panel $0.0162 + session-9
429-acceptance run $0.0201 + earlier P4.1 runs). Items 1–2 below are the
same two from session 8, now lower stakes; say the word and they're ticked.)

**Session-10 addendum:** your KYC bug report is **fixed and live-verified**.
beyondtech.com.tr re-analyzed on prod: KYC now reads defense/unmanned-systems
with the full BAZNA product line, and prompts are real user questions
("Who are the leading unmanned aerial vehicles manufacturers in Turkey?" +
two BAZNA-by-name brand probes). See item 0 below.

## Do now (recommended, no longer urgent)

- [ ] **0. Verify the KYC fix on your screen** (2 min):
  https://yanki.beyondkaira.com/analyses/9e4b2746-ae07-49f8-bf77-d2443ee4bac2
  — say if the prompt balance (8 category questions / 2 brand probes) or any
  shape needs tuning. Root cause was your site being a JS-rendered SPA: the
  crawler now mines your JS bundle for the real content.

- [ ] **1. Set hard spend caps in both provider consoles** (~5 min). Code-side
  rate limiting now bounds abuse at ≈$1.62/day, so this is defense-in-depth
  rather than the only barrier — still worth doing because only you can cap
  a *provider-side* surprise (pricing change, a bug on our side):
  - **Anthropic:** console.anthropic.com → Billing/Limits → monthly spend
    limit (e.g. $10).
  - **OpenAI:** platform.openai.com → Billing → usage limits (e.g. $10/mo).
  - Escape hatches any time: `ANALYSES_DAILY_CAP=0` in `deploy/.env` +
    `sg docker -c "make deploy"` → every submit 429s (kill-switch); or
    `DRY_RUN=1` + redeploy → $0 mock mode.
- [ ] **2. Eyeball the KYC card + live result** (2 minutes, no tooling):
  https://yanki.beyondkaira.com/analyses/17164747-a6a7-40ab-bc3b-d4d4d6e9ee62
  — score gauge, then the "Company profile (KYC)" card, then prompts and the
  response table. Say if you want the card's content or order changed.

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

## Later — Phase 5, the public checker (2/12 built; these come due at P5.7/P5.11)

- [ ] **12. Two more API keys** when P5.7/P5.11 come up (**~2–3 sessions
  away** at the current pace — P5.2–P5.6 need nothing from you):
  `GEMINI_API_KEY` + `PERPLEXITY_API_KEY`, plus a grounding/ToS sanity check
  for both.
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
