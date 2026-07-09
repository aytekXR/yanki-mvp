# Security Policy

Yanki is a public repository. The single most important rule:

## Never commit a secret

- All secrets (API keys, the Postgres password) live in `deploy/.env`, which is
  **gitignored**. Only `deploy/.env.example` — placeholders only — is tracked.
- `make deploy` refuses to run if `deploy/.env` is missing on the server and
  never auto-creates secrets.
- With `DRY_RUN=1` (the default) the whole pipeline runs on a mock provider, so
  no real keys are needed for local dev, tests, or CI.

If you believe a secret was committed, treat it as compromised: rotate the key
immediately, then remove it from history. Notify us (below) so we can help.

### Automated secret scanning

Automated secret scanning with **gitleaks** is wired up on two layers:

- **Pre-commit hook** (`.pre-commit-config.yaml`) — the `gitleaks` hook scans
  the staged diff and fails the commit on a leak. Installed by `make setup`.
- **CI job** (`.github/workflows/ci.yml`, the `secrets` job) — a
  checksum-pinned gitleaks scans the **full git history** on every push and
  pull request and fails the build on any finding.

Both are still a backstop, not a substitute for care: keep secrets in the
gitignored `deploy/.env` and never paste one into a tracked file.

## Reporting a vulnerability

Please report security issues privately to **aytek@beyondkaira.com** rather than
opening a public issue. Include steps to reproduce and the potential impact.
We'll acknowledge and work with you on a fix.
