# Operator Expected — your quick checklist

*The on-the-go version of [operator-actions.md](operator-actions.md) — full
context, commands, and the "why" live there; this file is just the tick-list.
Maintained by the orchestrator at every session close. Tick items as you do
them; the next session re-checks `deploy/.env`, the git remote, and CI status
at start regardless.*

Last updated: 2026-07-09 (session 2 close).

## Do now — everything else in Phase 4 waits on these

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
