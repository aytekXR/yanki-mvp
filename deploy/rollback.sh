#!/usr/bin/env bash
# =============================================================================
# Yanki prod rollback: redeploy the last-good SHA recorded by deploy.sh.
#
#   First exercised 2026-07-10 (P4.2): same-SHA rollback path ran clean and
#   healthy. The pruned-image branch (git checkout + rebuild) is still unproven.
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
# instead of falsely printing "complete". Port must match deploy.sh / the
# compose loopback bind (YANKI_PROD_API_PORT, default 8143).
API_PORT="$(grep -E '^YANKI_PROD_API_PORT=' "$HERE/.env" 2>/dev/null | tail -1 | cut -d= -f2 | tr -d '[:space:]\r' || true)"
API_PORT="${API_PORT:-8143}"
echo ">> health check: http://127.0.0.1:${API_PORT}/healthz"
healthy=0
for _ in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:${API_PORT}/healthz" >/dev/null 2>&1; then healthy=1; break; fi
  sleep 2
done

if [ "$healthy" -eq 1 ]; then
  echo ">> rollback to ${GIT_SHA} complete and healthy"
else
  echo "ERROR: rollback to ${GIT_SHA} failed its health check — inspect the server" >&2
  exit 1
fi
