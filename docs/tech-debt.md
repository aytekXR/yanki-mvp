# Technical Debt — living list

*Per [session-rules.md](session-rules.md): shortcuts are fine, hidden shortcuts
are not. Every session appends here and removes what it repays. Ordered
roughly by risk.*

Last updated: 2026-07-09 (session 2).

## Untested / never exercised

1. **`deploy/deploy.sh` + `rollback.sh` have never run against a real server.**
   Written to the ams-pulse pattern, `bash -n`-clean, logic reviewed (rollback
   rebuilds the last-good SHA via `git checkout`; check_env gate wired), but
   the first `make deploy` must be supervised. Cleared by P4.2.
2. **CI has never executed.** No GitHub remote is configured, so
   `.github/workflows/ci.yml` (five jobs: backend / frontend / contract-drift /
   secrets / e2e) is unproven — no job has ever run on a real runner. Cleared by
   pushing the repo (operator) + P4.3.
3. **Playwright e2e has never executed anywhere.** Chromium installs on this
   machine but can't launch without root `playwright install-deps`. The spec
   (`frontend/e2e/happy-path.spec.ts`) is written and gated on `E2E_BASE_URL`;
   the same flow passes via API-level curl e2e. The P4.4 `e2e` CI job is now
   authored (boots the DRY_RUN stack, `playwright install --with-deps chromium`,
   runs the spec against `:8140`) but has likewise never run. Cleared by pushing
   (CI runs it) or the operator's sudo (see
   [operator-actions.md](operator-actions.md)).
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

11. **`next lint` is deprecated (removed in Next 16) and now CI-blocking.** The
    frontend CI job's Lint step runs `npm run lint`, i.e. `next lint` (Next is
    pinned at `^15.1.0`). Migrating to the ESLint CLI is no longer optional: a
    Next 16 bump must land it in the same change or CI breaks.
12. **Node 20 on the dev host vs README's recommended 22 LTS** — everything
    green on 20; upgrade opportunistically.
13. **StepProgress / ResultsTable still have no behavior unit tests.** Partially
    repaid: both now carry axe a11y tests
    (`tests/StepProgress.a11y.test.tsx`, `tests/ResultsTable.a11y.test.tsx`), but
    nothing exercises their rendering logic. Add when they grow logic.
14. **gitleaks is pinned in two places that must move in lockstep.** `ci.yml`'s
    `secrets` job (`GITLEAKS_VERSION` + `GITLEAKS_SHA256`) and
    `.pre-commit-config.yaml` (`rev: v8.28.0`). Bump both together — and
    recompute the SHA256 from the release `checksums.txt` — or the CI layer and
    the local hook run different scanner versions.
15. **The pre-commit gitleaks hook is `language: golang`.** pre-commit
    auto-provisions its own Go toolchain to build it, so the first
    `pre-commit run` (or first commit) is heavy and needs network; an offline or
    otherwise constrained first run will stall. No system Go is required, and
    later runs are fast.
16. **Contrast fixes are guarded only by manually computed ratios.** axe's
    `color-contrast` rule is disabled under jsdom (it has no layout or paint —
    see `tests/a11y.ts`), so the P4.5 WCAG ratios are verified by hand, not by a
    running test. A token/color change that regresses contrast would pass CI.
    Re-check the ratios manually when touching the `*-soft` fills or the text
    tokens layered on them.
