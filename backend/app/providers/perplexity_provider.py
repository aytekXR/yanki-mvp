"""Perplexity stub provider.

Real Perplexity is out of scope for the MVP (see docs/02-mvp.md). This returns a
deterministic, plausible canned answer at $0 cost, and — like a real engine —
sometimes mentions no specific brand at all.
"""

from __future__ import annotations

import hashlib

from app.providers.base import ProviderResult

_ANSWERS = [
    "According to a broad search, commonly cited options include Acme, Globex "
    "and Wayne Enterprises.",
    "The sources I can draw on don't point to one definitive choice here.",
    "Frequently mentioned providers include Initech and Umbrella, but reviews "
    "are mixed and depend on the use case.",
    "Coverage is thin; no single provider stands out as the clear recommendation.",
]


class PerplexityProvider:
    name = "perplexity"
    model = "stub"

    def generate(self, prompt: str) -> ProviderResult:
        index = hashlib.sha256(prompt.encode("utf-8")).digest()[0] % len(_ANSWERS)
        return ProviderResult(text=_ANSWERS[index], model=self.model, cost_usd=0.0)
