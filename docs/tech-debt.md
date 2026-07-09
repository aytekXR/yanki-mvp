# Technical Debt — living list

*Per [session-rules.md](session-rules.md): shortcuts are fine, hidden shortcuts
are not. Every session appends here and removes what it repays. Ordered
roughly by risk.*

Last updated: 2026-07-09 (session 1).

## Untested / never exercised

1. **`deploy/deploy.sh` + `rollback.sh` have never run against a real server.**
   Written to the ams-pulse pattern, `bash -n`-clean, logic reviewed (rollback
   rebuilds the last-good SHA via `git checkout`; check_env gate wired), but
   the first `make deploy` must be supervised. Cleared by P4.2.
2. **CI has never executed.** No GitHub remote is configured, so
   `.github/workflows/ci.yml` (backend / frontend / contract-drift jobs) is
   unproven. Cleared by pushing the repo (operator) + P4.3.
3. **Playwright e2e blocked on this machine.** Chromium installs but can't
   launch without root `playwright install-deps`. The spec
   (`frontend/e2e/happy-path.spec.ts`) is written and gated on `E2E_BASE_URL`;
   the same flow passes via API-level curl e2e. Cleared by P4.4 (CI) or the
   operator's sudo (see [operator-actions.md](operator-actions.md)).
4. **Real Anthropic/OpenAI providers never called.** No live run, no cost
   validation (NFR-1 Week-1 invoice check pending — P4.1), and no
   respx-style contract tests asserting the real adapters' request/response
   shape. Price table in the providers is hardcoded from public pricing.

## Accepted MVP shortcuts (by design, revisit before/at launch)

5. **No rate limiting or per-IP quota on the anonymous `POST /api/v1/analyses`.**
   Per-job caps exist (`PROMPT_COUNT`, `MAX_RESPONSES_PER_JOB`), but nothing
   stops N parallel submissions. Fine while private; must land before any
   public URL with real keys (roadmap "Next": checker rate limits).
6. **DRY_RUN always analyzes the fixed mock company "Yanki Demo Co"**,
   regardless of the submitted URL (documented in architecture.md). Deliberate:
   keeps the mock deterministic end-to-end.
7. **Mock/KYC prompt coupling:** `providers/mock.py` returns the canned KYC
   profile when the prompt contains the substring `"json object"` — which
   `kyc.build_prompt` includes. Change one, keep the other in sync (both files
   carry comments).
8. **No intra-execute heartbeat.** `claimed_at` is heartbeated between steps,
   not inside the execute loop; an execute step longer than
   `STALE_CLAIM_SECONDS` (300s) could be reclaimed mid-run. Idempotent
   delete-before-rerun makes this safe but wasteful. Fix only if real runs
   approach 300s.
9. **`llm_cache` read-then-insert race** under concurrent workers could raise
   on the unique key. Single-worker MVP → not reachable today; guard with
   upsert when a second worker ships.
10. **`docker-compose.prod.yml` host ports are hard-bound** (127.0.0.1:8140/8141,
    not parameterized like dev). Intentional for the shared-Caddy topology;
    revisit if the server ever hosts a second Yanki instance.

## Hygiene / small

11. **gitleaks not yet wired** (SECURITY.md promises it; no
    `.pre-commit-config.yaml` exists). Part of P4.3.
12. **`next lint` is deprecated** (removed in Next 16); migrate to the ESLint
    CLI when bumping Next.
13. **Node 20 on the dev host vs README's recommended 22 LTS** — everything
    green on 20; upgrade opportunistically.
14. **StepProgress / ResultsTable have no dedicated unit tests** (reviewed,
    judged low-value now; the e2e covers them). Add when they grow logic.
