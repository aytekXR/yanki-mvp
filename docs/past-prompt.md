# Past Prompts

Archive of prompts already executed by AI-assisted development sessions.
Newest entry last. The active brief lives in `resume-prompt.md`.

---

## Session 1 — 2026-07-09

**Prompt executed:** "using workflows implement and follow @docs/resume-prompt.md"
(the founder-orchestrator brief, applied to the then-empty repo).

**Outcome:** Phases 0–3 delivered and verified in one orchestrated pass — see
[sessions/2026-07-09-01.md](sessions/2026-07-09-01.md). The next-session brief
lives at the end of that session log (§6).

---

## Session 2 — 2026-07-09

**Prompt executed:** "Using workflows, continue implementation. Is anything
expected from me? If so, log here and also to an operator expected md file.
Start from @docs/resume-prompt.md" — resolved via the session-1 brief
(sessions/2026-07-09-01.md §6): P4.1 was operator-blocked (no keys), so the
key-free alternates P4.3 + P4.5 ran, plus P4.4 authoring.

**Outcome:** P4.3 done (gitleaks in CI + pre-commit, red/green proven locally),
P4.4 authored (e2e CI job, unproven until first push), P4.5 done (9-finding
audit, 8 fixed, axe test layer added). See
[sessions/2026-07-09-02.md](sessions/2026-07-09-02.md); the next-session brief
lives at the end of that log (§6).

---

## Session 3 — 2026-07-09 → 07-10

**Prompt executed:** "Using workflows, continue implementation. Is anything
expected from me? If so, log here and also to a operator expected md file.
Start from @docs/resume-prompt.md" — resolved via the session-2 brief
(sessions/2026-07-09-02.md §6): both operator gates still closed (no
`deploy/.env` keys, no GitHub remote), so the neither-gate branch ran:
**P4.6** — decompose roadmap "Next" 2a into a Phase-5 task breakdown
(planning only).

**Outcome:** P4.6 done — Phase 5 (P5.1–P5.11, the free public checker) added to
implementation-plan.md with its build gate, lanes, and merge risks; no code
changed. See [sessions/2026-07-10-01.md](sessions/2026-07-10-01.md); the
next-session brief lives at the end of that log (§6).

---

## Session 4 — 2026-07-10

**Prompt executed:** "Using workflows, continue implementation. Is anything
expected from me? If so, log here and also to a operator expected md file.
Start from @docs/resume-prompt.md" — resolved via the session-3 brief
(sessions/2026-07-10-01.md §6) **as superseded by its §9 post-close
addendum**: the operator had pushed to GitHub and the first CI run was 4/5
green with e2e red, so the push-branch ran: fix the e2e job, prove all five
CI jobs green.

**Outcome:** e2e fixed (install-order: npm ci + Playwright before the
bind-mounting compose boot — dockerd was root-owning the anonymous-volume
mountpoint), verified locally by repro before pushing; run 29059944092 =
5/5 green with the Playwright spec's first-ever execution (`1 passed`,
6.6s) → P4.4 done; action majors bumped off Node 20 (checkout v7 /
setup-node v6 / setup-uv v7), run 29060093072 = 5/5 green, deprecation
annotations cleared. Tech-debt 2–3 repaid (list renumbered). See
[sessions/2026-07-10-02.md](sessions/2026-07-10-02.md); the next-session
brief lives at the end of that log (§6).

---

## Session 5 — 2026-07-10

**Prompt executed:** "Using workflows, continue implementation. Is anything
expected from me? IF so, log here and also to a operater expected md file.
Start from @docs/resume-prompt.md" — resolved via the session-4 brief
(sessions/2026-07-10-02.md §6): `deploy/.env` still had empty keys, so the
no-keys branch ran — the last key-free task, hygiene debt #10 (`next lint`
→ ESLint CLI).

**Outcome:** lint script migrated to `eslint . --ext .js,.jsx,.ts,.tsx
--max-warnings 0` with `next-env.d.ts` ignored (2-line diff, `fa13839`;
ESLint 8 + eslintrc deliberately kept, flat config + ESLint 9 deferred to
the Next 16 bump as new debt #16); verified by an exact local mirror of the
CI frontend job + adversarial review, then CI run 29062634057 = 5/5 green.
Old debt #10 repaid (hygiene tail renumbered). **No key-free work remains**
— everything now waits on the operator (keys → P4.1, then P4.2). See
[sessions/2026-07-10-03.md](sessions/2026-07-10-03.md); the next-session
brief lives at the end of that log (§6).

---

## Session 6 — 2026-07-10

**Prompts executed:** "which part of the roadmap is remained for the mvp? …
we will be serving the product from this vps on yanki.beyondkaira.com dns is
set. Put this also to the roadmap." (deploy retarget — landed as session-5
post-close addendum), then "Use the cheapist models from antropic and openai
x2", then "Just added the api keys" → per the standing brief, keys present ⇒
**P4.1**.

**Outcome:** OpenAI provider switched to `gpt-5-nano` ($0.05/$0.40; Anthropic
already on Haiku 4.5, the cheapest); **first live run completed** — real KYC +
`geo_score=0.2` for anthropic.com in ~40s, measured **$0.0132/analysis**
(Anthropic leg) ≈ 1% of the $49 plan (NFR-1 bar: <35%). Discovered the
operator's OpenAI key has `insufficient_quota` (new operator item 1b); the
OpenAI cost leg records after billing is fixed. P4.1 done → MVP 31/32 ≈ 97%,
readiness ~85%; only P4.2 (supervised deploy) remains. See
[sessions/2026-07-10-04.md](sessions/2026-07-10-04.md); the session-7 brief
lives at the end of that log (§6).

---

## Session 7 (2026-07-10, #05) — brief executed: the P4.2 branch

The session-7 brief (end of
[sessions/2026-07-10-04.md](sessions/2026-07-10-04.md) §6) offered two
branches: OpenAI re-run if quota existed (it didn't — still
`insufficient_quota`) and **P4.2 supervised deploy if the operator was
present** — the operator opened with "Let's deploy website. Using
workflows", so the deploy branch ran and completed: P4.2 done,
https://yanki.beyondkaira.com live, MVP 32/32. See
[sessions/2026-07-10-05.md](sessions/2026-07-10-05.md); the session-8 brief
(start Phase 5 / P5.1) lives at the end of that log (§6).

## Session 8 (2026-07-10, #06) — operator-directed: go live + KYC card

No archived brief ran verbatim: the operator opened with direct directives
("run mode: live-providers; KYC is very important — show it on the result
page; OpenAI is accessible now; Caddyfile pushed"), which superseded the
session-8 brief's P5.1 default. Delivered: KYC profile card
(implement+verify workflow, d75c852), prod flipped to DRY_RUN=0, first full
live panel on prod ($0.0162/analysis measured — P4.1 residual closed), and
P5.0 (rate-limit slice) added to the plan as the new first Phase-5 task.
See [sessions/2026-07-10-06.md](sessions/2026-07-10-06.md); the session-9
brief (P5.0 → P5.1) lives at the end of that log (§6).
