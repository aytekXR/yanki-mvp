from __future__ import annotations

import httpx
import pytest
import respx

from app.providers.base import Provider, ProviderResult
from app.providers.gemini_provider import (
    ENDPOINT,
    INPUT_PRICE_PER_TOKEN,
    OUTPUT_PRICE_PER_TOKEN,
    GeminiProvider,
)

_OK_BODY = {
    "candidates": [
        {
            "content": {
                "parts": [
                    {"text": "Popular options include Acme and "},
                    {"text": "Globex, based on a live search."},
                ]
            }
        }
    ],
    "usageMetadata": {
        "promptTokenCount": 120,
        "candidatesTokenCount": 30,
        "totalTokenCount": 150,
    },
}


def test_provider_satisfies_protocol():
    assert isinstance(GeminiProvider(api_key="k"), Provider)


@respx.mock
def test_generate_returns_text_and_nonzero_cost():
    route = respx.post(ENDPOINT).mock(return_value=httpx.Response(200, json=_OK_BODY))
    result = GeminiProvider(api_key="secret-key").generate("Who sells robots?")

    assert isinstance(result, ProviderResult)
    assert "Acme" in result.text and "Globex" in result.text
    assert result.model == "gemini-2.5-flash"

    expected = round(
        120 * INPUT_PRICE_PER_TOKEN + 30 * OUTPUT_PRICE_PER_TOKEN, 6
    )
    assert result.cost_usd == expected
    assert result.cost_usd > 0
    assert route.called


@respx.mock
def test_request_shape_has_grounding_and_auth_header():
    route = respx.post(ENDPOINT).mock(return_value=httpx.Response(200, json=_OK_BODY))
    GeminiProvider(api_key="secret-key").generate("Best CRM?")

    request = route.calls.last.request
    assert request.headers["x-goog-api-key"] == "secret-key"

    import json

    body = json.loads(request.content)
    # Search grounding must be present in the request body.
    assert body["tools"] == [{"google_search": {}}]
    assert body["contents"][0]["parts"][0]["text"] == "Best CRM?"


@respx.mock
def test_missing_candidates_yields_empty_text_and_zero_cost():
    body = {"candidates": [], "usageMetadata": {}}
    respx.post(ENDPOINT).mock(return_value=httpx.Response(200, json=body))
    result = GeminiProvider(api_key="k").generate("anything")
    assert result.text == ""
    assert result.cost_usd == 0.0


@respx.mock
def test_http_error_propagates():
    respx.post(ENDPOINT).mock(return_value=httpx.Response(500))
    with pytest.raises(httpx.HTTPStatusError):
        GeminiProvider(api_key="k").generate("boom")
