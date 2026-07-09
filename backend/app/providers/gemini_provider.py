"""Gemini stub provider.

Real Gemini is out of scope for the MVP (see docs/02-mvp.md). This returns a
deterministic, plausible canned answer at $0 cost, and — like a real engine —
sometimes mentions no specific brand at all.
"""

from __future__ import annotations

import hashlib

from app.providers.base import ProviderResult

_ANSWERS = [
    "Based on what is generally known, there are several credible providers in "
    "this space. Popular names include Acme, Globex and Initech.",
    "I do not have enough specific information to single out one option here.",
    "A few well-regarded choices come up often, such as Umbrella and Stark, "
    "though the best fit depends on your requirements.",
    "There isn't a clear single winner; the market has a healthy mix of "
    "established and newer players.",
]


class GeminiProvider:
    name = "gemini"
    model = "stub"

    def generate(self, prompt: str) -> ProviderResult:
        index = hashlib.sha256(prompt.encode("utf-8")).digest()[0] % len(_ANSWERS)
        return ProviderResult(text=_ANSWERS[index], model=self.model, cost_usd=0.0)
