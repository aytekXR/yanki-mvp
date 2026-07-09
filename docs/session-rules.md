# Session Rules

The operational checklist for every AI coding session in this repo. It is the
short distillation of [`resume-prompt.md`](resume-prompt.md) (the founder-
orchestrator brief). Read it start-to-finish before you touch code, and again
before you end the session. Scope authority is [`02-mvp.md`](02-mvp.md); cross-
agent mechanics are the master SPEC.

---

## 1. Session start ritual (do all of these first)

- [ ] Read [`../README.md`](../README.md) — the front door and Make targets.
- [ ] Read [`implementation-plan.md`](implementation-plan.md) — find the
      **current priority** and pick the next small task.
- [ ] Read [`tech-debt.md`](tech-debt.md) — know the known shortcuts before adding more.
- [ ] Read the **last entry** in [`sessions/`](sessions/) — the previous handoff.

## 2. During the session

- [ ] **Repo stays runnable** at every commit — `make dev` and `make test` never break.
- [ ] Ship **small vertical slices** (backend → API → db → frontend → tests → docs),
      not giant milestones.
- [ ] **Scope is frozen** to the in-scope flow in [`02-mvp.md`](02-mvp.md). New ideas
      go to [`roadmap.md`](roadmap.md)/backlog, never the current sprint.
- [ ] **Docs change in the same session as the code** — documentation never drifts.
- [ ] **Record assumptions explicitly** in the session log the moment you make them.
- [ ] **No secrets in git** — keys live in `deploy/.env` (gitignored); commit only
      `deploy/.env.example`.
- [ ] Stay inside your file-ownership set; never edit another agent's files.

## 3. Session end deliverables (all six — this is the handoff)

1. [ ] **Session summary** written to `sessions/YYYY-MM-DD-NN.md` (what/what changed/why).
2. [ ] **Documentation updates** — every affected doc in `docs/` brought in sync.
3. [ ] **Architectural changes** recorded as ADRs in [`design.md`](design.md)
       (why + consequences + migration notes).
4. [ ] **Technical debt** appended to [`tech-debt.md`](tech-debt.md) — shortcuts,
       hacks, TODOs, temporary implementations. Never hide debt.
5. [ ] **Current-state summary** — implemented / incomplete / blockers / assumptions.
6. [ ] **Next-session prompt** at the end of the session log, and the previous brief
       archived to [`past-prompt.md`](past-prompt.md). The next agent should need
       nothing beyond the repo + that prompt.

## 4. Definition of done (per task)

A task is done only when **all** are true:

- [ ] It **works** (verified, repo runnable).
- [ ] **Docs updated** in the same session.
- [ ] **Roadmap / implementation-plan status updated**.
- [ ] **Tech debt recorded** for anything left rough.
