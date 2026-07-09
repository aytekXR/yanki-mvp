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

### Planned hardening (tech debt)

Automated secret scanning with **gitleaks** (pre-commit hook + CI job) is
planned but not yet wired up — tracked in `docs/tech-debt.md`. Until then,
secret hygiene is enforced by review and `.gitignore`. Do not rely on tooling to
catch a leak for you.

## Reporting a vulnerability

Please report security issues privately to **aytek@beyondkaira.com** rather than
opening a public issue. Include steps to reproduce and the potential impact.
We'll acknowledge and work with you on a fix.
