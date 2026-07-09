#!/usr/bin/env bash
# =============================================================================
# Yanki prod deploy (ams-pulse pattern):
#   build -> tag by git SHA -> compose up -> migrate -> /healthz -> record
#   last-good SHA, auto-rollback on failure.
#
#   !!! UNTESTED — validate on the first server deploy. Marked tech debt. !!!
# =============================================================================
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"

COMPOSE="docker compose -p yanki-prod -f docker-compose.prod.yml"

# 1. Refuse to run without real secrets (never auto-create them).
if [ ! -f "$HERE/.env" ]; then
  echo "ERROR: $HERE/.env is missing." >&2
  echo "       cp deploy/.env.example deploy/.env and fill in real secrets first." >&2
  echo "       make deploy never auto-creates secrets." >&2
  exit 1
fi

# 2. Tag everything by the current git SHA.
GIT_SHA="$(git rev-parse --short HEAD)"
export GIT_SHA
echo ">> deploying yanki @ ${GIT_SHA}"

echo ">> building images (yanki-api:${GIT_SHA}, yanki-web:${GIT_SHA})"
$COMPOSE build

echo ">> starting stack"
$COMPOSE up -d

echo ">> running migrations (alembic upgrade head)"
$COMPOSE run --rm api alembic upgrade head

# 3. Health-check loop against the api.
echo ">> health check: http://127.0.0.1:8141/healthz"
healthy=0
for _ in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8141/healthz >/dev/null 2>&1; then healthy=1; break; fi
  sleep 2
done

# 4. Record last-good on success; auto-rollback on failure.
if [ "$healthy" -eq 1 ]; then
  echo "${GIT_SHA}" > "$HERE/.last-good"
  echo ">> deploy OK — recorded last-good = ${GIT_SHA}"
else
  echo "ERROR: health check failed — rolling back to last-good" >&2
  "$HERE/rollback.sh" || echo "ERROR: rollback also failed — inspect the server" >&2
  exit 1
fi
