#!/usr/bin/env bash
# Stop the yanki prod stack. Data volumes are kept (no `-v`).
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"

exec docker compose -p yanki-prod -f docker-compose.prod.yml down "$@"
