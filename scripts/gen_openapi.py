#!/usr/bin/env python3
"""Export the FastAPI OpenAPI schema to shared/contracts/openapi.json.

This is the first half of `make gen-types`; openapi-typescript then turns the
JSON into frontend/lib/types.ts. Keeping the schema checked in lets CI diff it,
so the FE/BE contract cannot silently drift (NFR-6).

Run via:  uv run --project backend python scripts/gen_openapi.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
OUT_PATH = REPO_ROOT / "shared" / "contracts" / "openapi.json"

# Make `import app...` resolve against the backend package.
sys.path.insert(0, str(BACKEND_DIR))


def main() -> None:
    # Imported here, after sys.path is set, so the backend app is importable.
    from app.api.main import app

    schema = app.openapi()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")
    print(f"wrote {OUT_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
