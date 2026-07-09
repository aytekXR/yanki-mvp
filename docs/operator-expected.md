# Operator Expected — your quick checklist

*The on-the-go version of [operator-actions.md](operator-actions.md) — full
context, commands, and the "why" live there; this file is just the tick-list.
Maintained by the orchestrator at every session close. Tick items as you do
them; the next session re-checks `deploy/.env`, the git remote, and CI status
at start regardless.*

Last updated: 2026-07-10 (session 3 close).

**Session 3 re-checked both gates: still closed — nothing NEW is blocking.**
Items 1–2 are the same two things as last session and still gate everything.
Session 3 spent the wait on P4.6 (the public-checker Phase-5 plan, P5.1–P5.11) —
that was the **last key-free task**, so from here every session opens by
checking items 1–2.

## Do now — everything else waits on these

- [ ] **1. Real API keys → unblocks P4.1 (cost validation), then P4.2 (deploy).**
  Spends real money, so timing is your call.
  ```bash
  cp deploy/.env.example deploy/.env
  # then edit: ANTHROPIC_API_KEY=…, OPENAI_API_KEY=…, DRY_RUN=0
  ```
- [ ] **2. Push to GitHub → first-ever CI run.**
  Create the repo (README assumes `github.com/Beyond-Kaira/yanki`), add the
  remote, push `main`. Then verify **all five** CI jobs go green:
  backend / frontend / contract / **secrets (gitleaks)** / **e2e (playwright)**.
  The e2e job has never run anywhere yet — expect it to be the most fragile.

## Optional

- [ ] **3. Local browser e2e needs root once** (skippable — CI covers it after
  item 2):
  ```bash
  cd frontend && sudo npx playwright install-deps chromium
  ```

## Later — at first deploy (P4.2, after items 1–2)

- [ ] **4. Server `deploy/.env`** from `.env.example` with real secrets
  (`POSTGRES_PASSWORD` must be set — `make deploy` refuses without it).
- [ ] **5. DNS A record:** `test.beyondkaira.com → 161.97.172.146`.
- [ ] **6. Caddy import:** drop `deploy/caddy/test.beyondkaira.com.caddy` into
  the shared pulse-prod import dir, `caddy validate`, then **reload** (never
  restart).
- [ ] **7. Supervise the first `make deploy`** — `deploy/deploy.sh` and
  `rollback.sh` have never run against a real server.

## Later — Phase 5, the public checker (only after the MVP is signed off)

- [ ] **8. Two more API keys** when P5.7/P5.11 come up: `GEMINI_API_KEY` +
  `PERPLEXITY_API_KEY` (plus a grounding/ToS sanity check for both).
- [ ] **9. Checker product decisions** (non-blocking today, needed before the
  checker goes live): who signs off the native Turkish (no sign-off → EN-only
  launch); the abuse thresholds (per-IP 5/h, per-brand 3/day, $50/day cap are
  guesses); email-gate strength (verification/captcha or not); which raw answer
  is shown free. Full context: [operator-actions.md](operator-actions.md) §
  "Phase-5 decisions" + the Phase-5 open questions in
  [implementation-plan.md](implementation-plan.md).
