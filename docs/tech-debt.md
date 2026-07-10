# Technical Debt — living list

*Per [session-rules.md](session-rules.md): shortcuts are fine, hidden shortcuts
are not. Every session appends here and removes what it repays. Ordered
roughly by risk.*

Last updated: 2026-07-10 (session 4: **items 2 and 3 repaid** — the e2e CI job
went green after the install-order fix and the Playwright spec had its
first-ever run, `1 passed (6.6s)` in run 29059944092 — and the list was
**renumbered** (old 4→2, 5→3, 6→4, 7→5, 8→6, 9→7, 10→8, 11→10, 12→11, 13→12,
14→13, 15→14, 16→15; archived session logs cite the old numbers). Two small
items added: #9 (e2e egress dependency) and #16 (`npm ci || npm install`
fallback).)

## Untested / never exercised

1. **`deploy/deploy.sh` + `rollback.sh` have never run against a real server.**
   Written to the ams-pulse pattern, `bash -n`-clean, logic reviewed (rollback
   rebuilds the last-good SHA via `git checkout`; check_env gate wired), but
   the first `make deploy` must be supervised. Cleared by P4.2.
2. **Real Anthropic/OpenAI providers never called.** No live run, no cost
   validation (NFR-1 Week-1 invoice check pending — P4.1), and no
   respx-style contract tests asserting the real adapters' request/response
   shape. Price table in the providers is hardcoded from public pricing.

## Accepted MVP shortcuts (by design, revisit before/at launch)

3. **No rate limiting or per-IP quota on the anonymous `POST /api/v1/analyses`.**
   Per-job caps exist (`PROMPT_COUNT`, `MAX_RESPONSES_PER_JOB`), but nothing
   stops N parallel submissions. Fine while private; must land before any
   public URL with real keys (roadmap "Next": checker rate limits).
   **Planned repayment: P5.6** (kill-switch + per-IP/per-brand limits + daily
   cost cap; decomposed session 3, not yet built).
4. **DRY_RUN always analyzes the fixed mock company "Yanki Demo Co"**,
   regardless of the submitted URL (documented in architecture.md). Deliberate:
   keeps the mock deterministic end-to-end.
5. **Mock/KYC prompt coupling:** `providers/mock.py` returns the canned KYC
   profile when the prompt contains the substring `"json object"` — which
   `kyc.build_prompt` includes. Change one, keep the other in sync (both files
   carry comments).
6. **No intra-execute heartbeat.** `claimed_at` is heartbeated between steps,
   not inside the execute loop; an execute step longer than
   `STALE_CLAIM_SECONDS` (300s) could be reclaimed mid-run. Idempotent
   delete-before-rerun makes this safe but wasteful. Fix only if real runs
   approach 300s.
7. **`llm_cache` read-then-insert race** under concurrent workers could raise
   on the unique key. Single-worker MVP → not reachable today; guard with
   upsert when a second worker ships. **Planned repayment: P5.2**'s
   `ON CONFLICT DO NOTHING` upsert (decomposed session 3, not yet built).
8. **`docker-compose.prod.yml` host ports are hard-bound** (127.0.0.1:8140/8141,
   not parameterized like dev). Intentional for the shared-Caddy topology;
   revisit if the server ever hosts a second Yanki instance.
9. **The e2e CI job depends on real runner egress to example.com.** DRY_RUN
   mocks only the LLM providers; pipeline step 1 (discovery) genuinely fetches
   the submitted URL, so the spec's `https://example.com` submission needs
   outbound network from the worker container. Accepted: hosted runners allow
   egress and example.com is highly stable; a red e2e *after green health
   waits* is a likely network flake, not an app regression (the job carries a
   comment saying so). Removing the dependency would mean mocking discovery
   under DRY_RUN or whitelisting a stack-served URL past the SSRF guard —
   both app changes made purely for CI; declined for the MVP.

## Hygiene / small

10. **`next lint` is deprecated (removed in Next 16) and now CI-blocking.** The
    frontend CI job's Lint step runs `npm run lint`, i.e. `next lint` (Next is
    pinned at `^15.1.0`). Migrating to the ESLint CLI is no longer optional: a
    Next 16 bump must land it in the same change or CI breaks. **This is the
    one remaining key-free fallback task** (session-5 brief).
11. **Node 20 on the dev host vs README's recommended 22 LTS** — everything
    green on 20; upgrade opportunistically.
12. **StepProgress / ResultsTable still have no behavior unit tests.** Partially
    repaid: both now carry axe a11y tests
    (`tests/StepProgress.a11y.test.tsx`, `tests/ResultsTable.a11y.test.tsx`), but
    nothing exercises their rendering logic. Add when they grow logic.
13. **gitleaks is pinned in two places that must move in lockstep.** `ci.yml`'s
    `secrets` job (`GITLEAKS_VERSION` + `GITLEAKS_SHA256`) and
    `.pre-commit-config.yaml` (`rev: v8.28.0`). Bump both together — and
    recompute the SHA256 from the release `checksums.txt` — or the CI layer and
    the local hook run different scanner versions.
14. **The pre-commit gitleaks hook is `language: golang`.** pre-commit
    auto-provisions its own Go toolchain to build it, so the first
    `pre-commit run` (or first commit) is heavy and needs network; an offline or
    otherwise constrained first run will stall. No system Go is required, and
    later runs are fast.
15. **Contrast fixes are guarded only by manually computed ratios.** axe's
    `color-contrast` rule is disabled under jsdom (it has no layout or paint —
    see `tests/a11y.ts`), so the P4.5 WCAG ratios are verified by hand, not by a
    running test. A token/color change that regresses contrast would pass CI.
    Re-check the ratios manually when touching the `*-soft` fills or the text
    tokens layered on them.
16. **`npm ci || npm install` fallback can mask lockfile drift.** Used in the
    frontend/contract/e2e CI jobs and both Dockerfiles (originally for the
    no-lockfile bootstrap). With `package-lock.json` now committed, a failing
    `npm ci` silently falls back to `npm install`, which may resolve different
    versions — a green job then doesn't prove the locked tree. Drop the
    fallback when convenient (low risk, low priority).
