#!/usr/bin/env bash
# Tail logs from the running yanki prod stack. Pass a service name to narrow,
# e.g. ./deploy/deploy-logs.sh api
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"

exec docker compose -p yanki-prod -f docker-compose.prod.yml logs -f --tail=100 "$@"
