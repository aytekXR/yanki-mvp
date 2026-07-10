"""Real Gemini provider via the REST ``generateContent`` endpoint.

Search grounding is enabled by sending the ``google_search`` tool in the request
body, so answers reflect a live web search (the checker's "four real engines"
promise). Auth is the ``x-goog-api-key`` header. Cost is estimated from the token
usage the API reports, using a pinned price-table constant. Only ever called when
``DRY_RUN`` is off; CI exercises it under ``respx`` and never makes a live call.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.providers.base import ProviderResult

MODEL = "gemini-2.5-flash"
MAX_OUTPUT_TOKENS = 1024
TIMEOUT_SECONDS = 30.0
ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{MODEL}:generateContent"
)

# Gemini 2.5 Flash list price: $0.30 / 1M input tokens, $2.50 / 1M output tokens.
# NOTE: grounded requests also carry a per-request Google Search fee (billed per
# grounded request, not per token) that is NOT modelled here — cost_usd is a
# token-only approximation. Exact retune against the live price tables is a P5.11
# week-1 read (tech-debt), consistent with ADR-22's cost-estimate caveat.
INPUT_PRICE_PER_TOKEN = 0.30 / 1_000_000
OUTPUT_PRICE_PER_TOKEN = 2.50 / 1_000_000


def _extract_text(data: dict[str, Any]) -> str:
    candidates = data.get("candidates") or []
    if not candidates:
        return ""
    parts = candidates[0].get("content", {}).get("parts", []) or []
    return "".join(part.get("text", "") for part in parts)


class GeminiProvider:
    name = "gemini"
    model = MODEL

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def generate(self, prompt: str) -> ProviderResult:
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            # Search grounding: the google_search tool makes the model answer
            # from a live web search rather than parametric memory only.
            "tools": [{"google_search": {}}],
            "generationConfig": {"maxOutputTokens": MAX_OUTPUT_TOKENS},
        }
        response = httpx.post(
            ENDPOINT,
            headers={"x-goog-api-key": self._api_key},
            json=payload,
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        text = _extract_text(data)
        usage = data.get("usageMetadata", {})
        prompt_tokens = usage.get("promptTokenCount", 0)
        output_tokens = usage.get("candidatesTokenCount", 0)
        cost = (
            prompt_tokens * INPUT_PRICE_PER_TOKEN
            + output_tokens * OUTPUT_PRICE_PER_TOKEN
        )
        return ProviderResult(text=text, model=self.model, cost_usd=round(cost, 6))
