# Technical Debt — living list

*Per [session-rules.md](session-rules.md): shortcuts are fine, hidden shortcuts
are not. Every session appends here and removes what it repays. Ordered
roughly by risk.*

Last updated: 2026-07-10 (session 6: **item 2 rewritten** — first live run;
Anthropic leg proven, OpenAI leg blocked on operator quota, KYC-cost gap
noted. Earlier session 5: **item 10 repaid** — the frontend `lint`
script now calls the ESLint CLI directly (`eslint . --ext .js,.jsx,.ts,.tsx
--max-warnings 0`), verified by mirroring the CI frontend job locally and on
the real runner (run 29062634057) — and the hygiene tail was **renumbered
again** (old 11→10, 12→11, 13→12, 14→13, 15→14, 16→15; items 1–9 unchanged;
the session-4 header carried the previous map, archived logs cite the numbers
of their day). One new item: #16 (flat config + ESLint 9 deferred to the
Next 16 bump). Post-close: #8 rewritten — deploy retargeted to
`yanki.beyondkaira.com` on the shared VPS; prod ports parameterized and the
shared-Caddy network wiring added, all unexercised until P4.2.)

## Untested / never exercised

1. **`deploy/deploy.sh` + `rollback.sh` have never run against a real server.**
   Written to the ams-pulse pattern, `bash -n`-clean, logic reviewed (rollback
   rebuilds the last-good SHA via `git checkout`; check_env gate wired), but
   the first `make deploy` must be supervised. Cleared by P4.2.
2. **Real-provider coverage is half-proven (Anthropic ✅ live, OpenAI ❌).**
   Session 6 (2026-07-10) ran the pipeline live: the Anthropic adapter
   (Claude Haiku 4.5) worked end-to-end — real KYC + 10 panel responses,
   `cost_usd` math validated against reported usage ($0.0132/analysis).
   Remaining: (a) the **OpenAI adapter (`gpt-5-nano`) has never returned a
   successful response** — the operator's key has `insufficient_quota`, so
   the new `max_completion_tokens` + `reasoning_effort="minimal"` params are
   verified against docs but not live (the 429s prove auth + endpoint + SDK
   plumbing work); re-run once quota exists. (b) The **KYC call's cost is
   not persisted** — `responses.cost_usd` covers the panel only, so the
   recorded per-analysis cost understates by ~1 call (~$0.002 at Haiku
   prices with page text as input); fold KYC cost into the analysis row if
   precise invoicing ever matters. (c) Still no respx-style contract tests
   for the adapters; price tables remain hardcoded from (now verified)
   public pricing.

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
8. **The prod Caddy wiring is designed from inspection, never exercised.**
   Session-5 post-close (deploy retargeted to `yanki.beyondkaira.com` on the
   shared VPS): the old hard-bound 127.0.0.1:8140/8141 ports were replaced —
   web/api now join the shared Caddy's network (`pulse-prod_default`,
   `external:`) as `yanki-web`/`yanki-api`, with parameterized loopback binds
   (8142/8143) for health checks only. Couplings to know: the Caddy
   snippet's aliases must match the compose aliases (edited by hand in two
   repos); the pulse-prod stack must be up or `compose up` fails on the
   missing external network; the coupling is TWO-WAY — while yanki-prod is
   attached, a `pulse-prod down`/network recreate is blocked by (or strands)
   yanki's endpoints; and none of it has run yet — P4.2's supervised deploy
   proves it (or amends it). The snippet itself `caddy validate`s clean,
   standalone and concatenated with the live shared Caddyfile (2026-07-10,
   same caddy:2 image digest as the running container).
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

10. **Node 20 on the dev host vs README's recommended 22 LTS** — everything
    green on 20; upgrade opportunistically.
11. **StepProgress / ResultsTable still have no behavior unit tests.** Partially
    repaid: both now carry axe a11y tests
    (`tests/StepProgress.a11y.test.tsx`, `tests/ResultsTable.a11y.test.tsx`), but
    nothing exercises their rendering logic. Add when they grow logic.
12. **gitleaks is pinned in two places that must move in lockstep.** `ci.yml`'s
    `secrets` job (`GITLEAKS_VERSION` + `GITLEAKS_SHA256`) and
    `.pre-commit-config.yaml` (`rev: v8.28.0`). Bump both together — and
    recompute the SHA256 from the release `checksums.txt` — or the CI layer and
    the local hook run different scanner versions.
13. **The pre-commit gitleaks hook is `language: golang`.** pre-commit
    auto-provisions its own Go toolchain to build it, so the first
    `pre-commit run` (or first commit) is heavy and needs network; an offline or
    otherwise constrained first run will stall. No system Go is required, and
    later runs are fast.
14. **Contrast fixes are guarded only by manually computed ratios.** axe's
    `color-contrast` rule is disabled under jsdom (it has no layout or paint —
    see `tests/a11y.ts`), so the P4.5 WCAG ratios are verified by hand, not by a
    running test. A token/color change that regresses contrast would pass CI.
    Re-check the ratios manually when touching the `*-soft` fills or the text
    tokens layered on them.
15. **`npm ci || npm install` fallback can mask lockfile drift.** Used in the
    frontend/contract/e2e CI jobs and both Dockerfiles (originally for the
    no-lockfile bootstrap). With `package-lock.json` now committed, a failing
    `npm ci` silently falls back to `npm install`, which may resolve different
    versions — a green job then doesn't prove the locked tree. Extra edge since
    session 5: a fallback `npm install` could pull a newer in-range
    eslint-config-next whose new warnings would trip the `--max-warnings 0`
    gate in a way the committed lockfile can't reproduce. Drop the fallback
    when convenient (low risk, low priority).
16. **ESLint 8.57 (EOL) + legacy `.eslintrc.json` deliberately kept; flat
    config + ESLint 9 deferred to the Next 16 bump.** Session 5 repaid old
    debt #10 with the minimal-risk diff: only the `lint` script changed
    (`next lint` → `eslint . --ext .js,.jsx,.ts,.tsx --max-warnings 0`), so
    the Next-16-blocking `next lint` call is gone with zero dependency/lockfile
    churn. The deferred half: `--ext` and `.eslintrc.json` BOTH stop working
    under ESLint 9's flat config, so the Next 16 / eslint-config-next 16 bump
    must swap in an `eslint.config.mjs` (FlatCompat pattern, port
    `ignorePatterns` → `ignores`) and drop `--ext` in the same change — plan it
    manually, the official `next-lint-to-eslint-cli` codemod's legacy-config
    conversion is buggy (vercel/next.js#85679). Two accepted quirks meanwhile:
    `--max-warnings 0` is deliberately stricter than `next lint` (warnings now
    fail CI — treat a future warning-level failure as a real gate, not a
    flake), and `postcss.config.mjs` stays unlinted (`.mjs` not in `--ext`;
    `next lint` never covered it either). Note: Next 16 also stops linting
    during `next build`, making this script the ONLY lint gate.
