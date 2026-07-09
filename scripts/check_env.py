#!/usr/bin/env python3
"""Tiny sanity check for the environment file.

Exits non-zero only when DRY_RUN is off but a required LLM key is missing —
the one mistake that turns a "free" run into a broken (or costly) one.

Usage:  python scripts/check_env.py [path/to/.env]   (default: deploy/.env)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

REQUIRED_WHEN_LIVE = ("ANTHROPIC_API_KEY", "OPENAI_API_KEY")
TRUTHY = {"1", "true", "yes", "on"}


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        values[key.strip()] = val.strip()
    return values


def main() -> int:
    env_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("deploy/.env")
    # Process env overrides the file (compose/host precedence).
    values = {**load_env_file(env_path), **os.environ}

    if values.get("DRY_RUN", "1").lower() in TRUTHY:
        print("check_env: DRY_RUN is on — no API keys required. OK.")
        return 0

    missing = [key for key in REQUIRED_WHEN_LIVE if not values.get(key)]
    if missing:
        print(
            "check_env: DRY_RUN is off but these keys are empty: "
            + ", ".join(missing),
            file=sys.stderr,
        )
        return 1

    print("check_env: real-provider config looks complete. OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
