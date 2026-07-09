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
# If they were pruned, rebuild from the currently checked-out tree (best effort).
if [ -z "$(docker images -q "yanki-api:${GIT_SHA}")" ]; then
  echo ">> yanki-api:${GIT_SHA} not found locally — rebuilding from current tree"
  $COMPOSE build
fi

$COMPOSE up -d
echo ">> rollback to ${GIT_SHA} complete"
