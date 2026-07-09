#!/usr/bin/env bash
# =============================================================================
# Yanki prod rollback: redeploy the last-good SHA recorded by deploy.sh.
#
#   !!! UNTESTED — validate on the first server deploy. Marked tech debt. !!!
# =============================================================================
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"

COMPOSE="docker compose -p yanki-prod -f docker-compose.prod.yml"

if [ ! -f "$HERE/.last-good" ]; then
  echo "ERROR: no $HERE/.last-good — there is no known-good release to roll back to." >&2
  exit 1
fi

GIT_SHA="$(cat "$HERE/.last-good")"
export GIT_SHA
echo ">> rolling back to ${GIT_SHA}"

# The last-good images should already be built locally from the prior deploy.
# If they were pruned, rebuild — but check out the last-good SHA first, so we
# rebuild the KNOWN-GOOD code, not whatever broken tree triggered this rollback.
if [ -z "$(docker images -q "yanki-api:${GIT_SHA}")" ]; then
  echo ">> yanki-api:${GIT_SHA} not found locally — checking it out and rebuilding"
  git checkout "${GIT_SHA}"
  $COMPOSE build
fi

$COMPOSE up -d

# Verify the rollback actually came up, so a failed rollback exits non-zero
# instead of falsely printing "complete".
echo ">> health check: http://127.0.0.1:8141/healthz"
healthy=0
for _ in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8141/healthz >/dev/null 2>&1; then healthy=1; break; fi
  sleep 2
done

if [ "$healthy" -eq 1 ]; then
  echo ">> rollback to ${GIT_SHA} complete and healthy"
else
  echo "ERROR: rollback to ${GIT_SHA} failed its health check — inspect the server" >&2
  exit 1
fi
