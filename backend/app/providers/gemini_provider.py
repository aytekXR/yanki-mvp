"""Real Gemini provider via the REST ``generateContent`` endpoint.

Search grounding is enabled by sending the ``google_search`` tool in the request
body, so answers reflect a live web search (the checker's "four real engines"
promise). Auth is the ``x-goog-api-key`` header. Cost is estimated from the token
usage the API reports, using a pinned price-table constant. Only ever called when
``DRY_RUN`` is off; CI exercises it under ``respx`` and never makes a live call.

Resilience (added after the P5.7 live incident, see ADR-23 addendum):
- **Model** is the rolling alias ``gemini-flash-lite-latest``. Pinned models can
  be retired for *new* accounts while still appearing in ``ListModels`` (a live
  incident: ``gemini-2.5-flash`` listed but 404s on ``generateContent`` for a new
  key), so a pinned id is not a safe availability signal.
- **Grounded-to-ungrounded fallback with a memo.** A free-tier key has zero
  Google-Search-grounding quota and 429s on any grounded request. We try grounded
  first; on 429 we retry the same prompt *without* tools and set a process-wide
  flag so the remaining prompts in this run skip the grounded attempt entirely
  (a 12-prompt run must not pay 12 failed grounded attempts). The flag is reset
  by a worker restart, so once the operator enables billing and redeploys, the
  next process re-tries grounded once and — with quota — sticks with it.
- **Bounded transient retry.** A 503/5xx or an ``httpx`` timeout is retried once
  after a short sleep, then raised.
- The reported ``model`` string carries a ``:grounded`` / ``:ungrounded`` marker
  so the ResultsTable surfaces when an answer ran without live search.
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from app.providers.base import ProviderResult

# Rolling alias, not a pinned id: a pinned Gemini model can be retired for new
# accounts while still listed by ListModels (the P5.7 incident), and the lite
# tier matches the operator's standing cheapest-models directive. Alias price
# drift is acceptable inside the existing cost-approximation caveat (tech-debt
# 23). This stays the single source of truth for the model name; the reported
# ProviderResult.model appends a grounding marker (see ``generate``).
MODEL = "gemini-flash-lite-latest"
MAX_OUTPUT_TOKENS = 1024
TIMEOUT_SECONDS = 30.0
RETRY_SLEEP_SECONDS = 2.0
ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{MODEL}:generateContent"
)

# UNVERIFIED placeholder prices for the flash-lite tier: $0.10 / 1M input tokens,
# $0.40 / 1M output tokens. The rolling alias may drift tiers under us and these
# are a best-effort stand-in, not a read of the live price tables. Grounded
# requests also carry a per-request Google Search fee that is NOT modelled here —
# cost_usd stays a token-only approximation. tech-debt 23 and operator item B2
# own the exact retune (same caveat as ADR-22's cost estimate).
INPUT_PRICE_PER_TOKEN = 0.10 / 1_000_000
OUTPUT_PRICE_PER_TOKEN = 0.40 / 1_000_000


def _extract_text(data: dict[str, Any]) -> str:
    candidates = data.get("candidates") or []
    if not candidates:
        return ""
    parts = candidates[0].get("content", {}).get("parts", []) or []
    return "".join(part.get("text", "") for part in parts)


class GeminiProvider:
    name = "gemini"
    model = MODEL

    # Process-wide memo: once a grounded request has been rejected with 429 in
    # this process, every later call skips the grounded attempt. Reset on worker
    # restart, so enabling billing then redeploying re-tries grounded once.
    _grounding_disabled = False

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def _payload(self, prompt: str, *, grounded: bool) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": MAX_OUTPUT_TOKENS},
        }
        if grounded:
            # Search grounding: the google_search tool makes the model answer
            # from a live web search rather than parametric memory only.
            payload["tools"] = [{"google_search": {}}]
        return payload

    def _request(self, payload: dict[str, Any]) -> httpx.Response:
        """POST once, retrying a single time on a 5xx or timeout after a sleep.

        4xx responses are returned as-is for the caller to handle (the 429
        grounded-to-ungrounded fallback lives in ``generate``).
        """
        response: httpx.Response | None = None
        for attempt in range(2):
            try:
                response = httpx.post(
                    ENDPOINT,
                    headers={"x-goog-api-key": self._api_key},
                    json=payload,
                    timeout=TIMEOUT_SECONDS,
                )
            except httpx.TimeoutException:
                if attempt == 0:
                    time.sleep(RETRY_SLEEP_SECONDS)
                    continue
                raise
            if response.status_code >= 500 and attempt == 0:
                time.sleep(RETRY_SLEEP_SECONDS)
                continue
            return response
        assert response is not None  # loop always assigns or raises
        return response

    def generate(self, prompt: str) -> ProviderResult:
        use_grounding = not GeminiProvider._grounding_disabled
        response = self._request(self._payload(prompt, grounded=use_grounding))
        grounded = use_grounding

        if use_grounding and response.status_code == 429:
            # Free-tier keys have zero Search-grounding quota. Fall back to an
            # ungrounded request and memo it so the rest of this run skips the
            # grounded attempt (worker restart re-tries once with billing on).
            GeminiProvider._grounding_disabled = True
            grounded = False
            response = self._request(self._payload(prompt, grounded=False))

        response.raise_for_status()
        data = response.json()
        text = _extract_text(data)

        usage = data.get("usageMetadata", {})
        prompt_tokens = usage.get("promptTokenCount", 0)
        # Thinking tokens (gemini-3 family) bill as output; fold them in.
        output_tokens = usage.get("candidatesTokenCount", 0) + usage.get(
            "thoughtsTokenCount", 0
        )
        cost = (
            prompt_tokens * INPUT_PRICE_PER_TOKEN
            + output_tokens * OUTPUT_PRICE_PER_TOKEN
        )

        marker = ":grounded" if grounded else ":ungrounded"
        return ProviderResult(
            text=text, model=f"{MODEL}{marker}", cost_usd=round(cost, 6)
        )
