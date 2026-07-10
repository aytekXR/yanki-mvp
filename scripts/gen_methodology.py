#!/usr/bin/env python3
"""Export the checker methodology to shared/contracts/checker_methodology.json.

This is the third artifact produced by `make gen-types` (alongside
openapi.json → types.ts). The public `/methodology` page imports this JSON at
build time and renders the exact prompts, engines, and score formula the runner
actually uses — so the published "show our work" page can never drift from the
code. It is GENERATED, never hand-edited; CI's contract-drift gate diffs it.

The 12 prompts are read straight from the version-stamped
``app.pipeline.checker_prompts`` module (the same one the runner executes),
built against an empty KYC so the neutral fallback terms ("solutions",
"worldwide", "the market leaders") stand in for the per-brand category/location/
competitor the runner substitutes live. Editing a prompt template and rerunning
`make gen-types` re-exports here with no second edit.

Run via:  uv run --project backend python scripts/gen_methodology.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
OUT_PATH = REPO_ROOT / "shared" / "contracts" / "checker_methodology.json"

# Make `import app...` resolve against the backend package.
sys.path.insert(0, str(BACKEND_DIR))


def main() -> None:
    # Imported here, after sys.path is set, so the backend app is importable.
    from app.pipeline.checker_prompts import VERSION, generate
    from app.pipeline.kyc import KYC
    from app.providers.registry import DEFAULT_PANEL

    # An empty KYC yields the deterministic neutral fallbacks, so the exported
    # strings show the real question shapes with a stand-in category term.
    sample_kyc = KYC(company="")
    prompts = [
        {"index": i + 1, "text": spec.text, "category": spec.category}
        for i, spec in enumerate(generate(sample_kyc, lang="en"))
    ]

    artifact = {
        "version": VERSION,
        "language": "en",
        "engines": list(DEFAULT_PANEL),
        "prompts": prompts,
        "score_formula": {
            "expression": "footprints / total_responses",
            "numerator": "footprints",
            "denominator": "total_responses",
            "range": "0.0 to 1.0",
            "description": (
                "The share of engine answers that mentioned the brand: the count "
                "of answers with a footprint divided by the total answers collected."
            ),
        },
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n")
    print(f"wrote {OUT_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
