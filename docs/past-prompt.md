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
