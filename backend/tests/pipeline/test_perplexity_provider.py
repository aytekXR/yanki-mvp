from __future__ import annotations

import json

import httpx
import pytest
import respx

from app.providers.base import Provider, ProviderResult
from app.providers.perplexity_provider import (
    ENDPOINT,
    INPUT_PRICE_PER_TOKEN,
    OUTPUT_PRICE_PER_TOKEN,
    PerplexityProvider,
)

_OK_BODY = {
    "choices": [
        {"message": {"role": "assistant", "content": "Commonly cited: Acme, Globex."}}
    ],
    "usage": {"prompt_tokens": 200, "completion_tokens": 40, "total_tokens": 240},
}


def test_provider_satisfies_protocol():
    assert isinstance(PerplexityProvider(api_key="k"), Provider)


@respx.mock
def test_generate_returns_text_and_nonzero_cost():
    route = respx.post(ENDPOINT).mock(return_value=httpx.Response(200, json=_OK_BODY))
    result = PerplexityProvider(api_key="secret-key").generate("Who sells robots?")

    assert isinstance(result, ProviderResult)
    assert "Acme" in result.text and "Globex" in result.text
    assert result.model == "sonar"

    expected = round(
        200 * INPUT_PRICE_PER_TOKEN + 40 * OUTPUT_PRICE_PER_TOKEN, 6
    )
    assert result.cost_usd == expected
    assert result.cost_usd > 0
    assert route.called


@respx.mock
def test_request_shape_has_model_and_bearer_auth():
    route = respx.post(ENDPOINT).mock(return_value=httpx.Response(200, json=_OK_BODY))
    PerplexityProvider(api_key="secret-key").generate("Best CRM?")

    request = route.calls.last.request
    assert request.headers["authorization"] == "Bearer secret-key"

    body = json.loads(request.content)
    assert body["model"] == "sonar"
    assert body["messages"] == [{"role": "user", "content": "Best CRM?"}]


@respx.mock
def test_null_content_yields_empty_text():
    body = {
        "choices": [{"message": {"role": "assistant", "content": None}}],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0},
    }
    respx.post(ENDPOINT).mock(return_value=httpx.Response(200, json=body))
    result = PerplexityProvider(api_key="k").generate("anything")
    assert result.text == ""
    assert result.cost_usd == 0.0


@respx.mock
def test_http_error_propagates():
    respx.post(ENDPOINT).mock(return_value=httpx.Response(500))
    with pytest.raises(httpx.HTTPStatusError):
        PerplexityProvider(api_key="k").generate("boom")
