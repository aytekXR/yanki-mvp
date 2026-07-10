"""Real Perplexity provider via the ``chat/completions`` REST endpoint.

Model ``sonar`` is Perplexity's search-grounded chat model (it answers from a
live web search by default), reached with Bearer auth. Cost is estimated from the
token usage the API reports, using a pinned price-table constant. Only ever
called when ``DRY_RUN`` is off; CI exercises it under ``respx`` and never makes a
live call.
"""

from __future__ import annotations

import httpx

from app.providers.base import ProviderResult

MODEL = "sonar"
MAX_TOKENS = 1024
TIMEOUT_SECONDS = 30.0
ENDPOINT = "https://api.perplexity.ai/chat/completions"

# Perplexity `sonar` list price: $1.00 / 1M input tokens, $1.00 / 1M output
# tokens. NOTE: sonar also bills a per-request search fee (priced by request /
# context tier, not tokens) that is NOT modelled here — cost_usd is a token-only
# approximation. Exact retune against the live price tables is a P5.11 week-1
# read (tech-debt), consistent with ADR-22's cost-estimate caveat.
INPUT_PRICE_PER_TOKEN = 1.00 / 1_000_000
OUTPUT_PRICE_PER_TOKEN = 1.00 / 1_000_000


class PerplexityProvider:
    name = "perplexity"
    model = MODEL

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def generate(self, prompt: str) -> ProviderResult:
        payload = {
            "model": MODEL,
            "max_tokens": MAX_TOKENS,
            "messages": [{"role": "user", "content": prompt}],
        }
        response = httpx.post(
            ENDPOINT,
            headers={"Authorization": f"Bearer {self._api_key}"},
            json=payload,
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        text = data["choices"][0]["message"].get("content") or ""
        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        cost = (
            prompt_tokens * INPUT_PRICE_PER_TOKEN
            + completion_tokens * OUTPUT_PRICE_PER_TOKEN
        )
        return ProviderResult(text=text, model=self.model, cost_usd=round(cost, 6))
