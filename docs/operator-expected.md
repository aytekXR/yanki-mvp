# Operator Expected — everything only a human can do

*The single operator file (the former `operator-actions.md` was merged in
here, 2026-07-10). Maintained by the orchestrator at every session close.
Tick items as you do them; the next session re-checks `deploy/.env`, the git
remote, and CI status at start regardless. Nothing here blocks local
development — `make dev` + `make test` work with zero keys and zero cost
(DRY_RUN).*

Last updated: 2026-07-10 (session 11: **items 0–2 all confirmed done by
you — thank you. Nothing is expected from you right now.** Your follow-up
"show full LLM responses, on demand" is being shipped this session:
expandable rows in the response table, collapsed by default. Your KYC
question answered: **nothing is hardcoded on prod — we really visit the
site.** The pipeline's discovery step fetches your actual website (homepage
+ up to 5 same-domain pages; for JS-rendered SPA sites it also mines the
site's own JS bundles for the embedded text), assembles ~20k chars of real
site text, and ONE live LLM call (Claude Haiku 4.5) extracts the profile
from that text under facts-only instructions — empty fields are preferred
over guesses, and an empty location backfills from the domain (.com.tr →
Türkiye). The only hardcoded profile anywhere is the deterministic mock
used by `DRY_RUN=1` dev/CI runs, which prod does not use.)

## Do now

Nothing. All operator items are done or parked (items 12–14 below come due
at P5.7/P5.11).

## Done (this session and before)

- [x] **0. KYC fix verified on the operator's screen** (2026-07-10,
  session 11): beyondtech.com.tr profile confirmed correct.
- [x] **1. Provider-console spend caps in place: $10** on both Anthropic
  and OpenAI (2026-07-10, session 11). Combined with code-side limits
  (5/IP/hour, 100/day ≈ $1.62/day worst case), the maximum blast radius is
  now doubly bounded. Escape hatches remain: `ANALYSES_DAILY_CAP=0` +
  redeploy (429 kill-switch) or `DRY_RUN=1` + redeploy ($0 mock).
- [x] **2. KYC card design reviewed** — good for now; operator will
  integrate a UI design (brandkit) later, so no card changes requested.
  Follow-up shipped instead: full LLM answers viewable on demand in the
  response table (this session).

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
