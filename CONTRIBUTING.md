# Contributing to Yanki

Thanks for helping build Yanki. The bar is simple: **`main` is always green and
always runnable.** Keep changes small and boring.

Read [`docs/session-rules.md`](docs/session-rules.md) first — it is the
operational checklist for every session (scope, ownership, definition of done).

## Branch & PR flow

1. Branch off `main`: `git checkout -b <type>/<short-topic>`
   (e.g. `feat/score-gauge`, `fix/worker-stale-claim`).
2. Ship a **small vertical slice** — one focused change, not a giant milestone.
3. Open a PR into `main`. The template prompts you for the checklist below.
4. Merge only when CI is green.

## Commits

- Small, self-contained commits — each one leaves the repo runnable.
- Conventional-ish subject lines: `type: summary` in the imperative mood, e.g.
  `feat: add ScoreGauge`, `fix: reclaim stale worker jobs`, `docs: update deploy`.
  Common types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`.

## Before you push

Run the same checks CI runs:

```bash
make fmt        # auto-format (ruff + prettier)
make lint       # ruff + eslint
make typecheck  # mypy + tsc
make test       # backend (pytest) + frontend (vitest)
```

If you changed the API contract (any Pydantic request/response schema), also run
`make gen-types` and commit the regenerated `shared/contracts/openapi.json` and
`frontend/lib/types.ts`. CI fails on contract drift.

## Two rules that never bend

- **Docs change with the code.** Update the affected `docs/` in the same PR;
  documentation must never drift from reality.
- **No secrets in git.** Real values live in `deploy/.env` (gitignored). Only
  commit `deploy/.env.example` with placeholders. See
  [`SECURITY.md`](SECURITY.md).

## Ownership

A file's owner is the owner of the directory it lives in. Anything under
`deploy/`, `.github/`, `shared/contracts/`, or `backend/alembic/` also needs the
lead's review. See [`docs/design.md`](docs/design.md) for the full map.
