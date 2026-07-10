from __future__ import annotations

import json

import httpx
import pytest
import respx

from app.providers.base import Provider, ProviderResult
from app.providers.gemini_provider import (
    ENDPOINT,
    INPUT_PRICE_PER_TOKEN,
    MODEL,
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


@pytest.fixture(autouse=True)
def _reset_grounding_memo():
    """The grounding memo is process-wide; reset it around every test."""
    GeminiProvider._grounding_disabled = False
    yield
    GeminiProvider._grounding_disabled = False


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    """Neutralise the transient-retry backoff so tests stay fast."""
    monkeypatch.setattr("app.providers.gemini_provider.time.sleep", lambda _s: None)


def test_provider_satisfies_protocol():
    assert isinstance(GeminiProvider(api_key="k"), Provider)


@respx.mock
def test_generate_returns_text_and_nonzero_cost():
    route = respx.post(ENDPOINT).mock(return_value=httpx.Response(200, json=_OK_BODY))
    result = GeminiProvider(api_key="secret-key").generate("Who sells robots?")

    assert isinstance(result, ProviderResult)
    assert "Acme" in result.text and "Globex" in result.text
    assert result.model == f"{MODEL}:grounded"
    assert MODEL == "gemini-flash-lite-latest"

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
    # A 4xx that is not a grounded 429 is raised, not retried.
    respx.post(ENDPOINT).mock(return_value=httpx.Response(400))
    with pytest.raises(httpx.HTTPStatusError):
        GeminiProvider(api_key="k").generate("boom")


@respx.mock
def test_grounded_429_falls_back_to_ungrounded_and_sets_memo():
    # First request (grounded) 429s; the retry (ungrounded) succeeds.
    route = respx.post(ENDPOINT).mock(
        side_effect=[
            httpx.Response(429, json={"error": {"status": "RESOURCE_EXHAUSTED"}}),
            httpx.Response(200, json=_OK_BODY),
        ]
    )
    provider = GeminiProvider(api_key="k")
    result = provider.generate("Who sells robots?")

    assert "Acme" in result.text
    assert result.model == f"{MODEL}:ungrounded"
    assert GeminiProvider._grounding_disabled is True
    assert route.call_count == 2

    grounded_body = json.loads(route.calls[0].request.content)
    fallback_body = json.loads(route.calls[1].request.content)
    assert "tools" in grounded_body
    assert "tools" not in fallback_body


@respx.mock
def test_second_call_after_memo_skips_grounded_attempt():
    route = respx.post(ENDPOINT).mock(
        side_effect=[
            httpx.Response(429, json={"error": {}}),
            httpx.Response(200, json=_OK_BODY),
            httpx.Response(200, json=_OK_BODY),
        ]
    )
    provider = GeminiProvider(api_key="k")
    provider.generate("first prompt")  # 429 grounded -> ungrounded fallback
    assert route.call_count == 2

    result = provider.generate("second prompt")
    # The memo means the second call makes exactly ONE request, ungrounded.
    assert route.call_count == 3
    assert result.model == f"{MODEL}:ungrounded"
    third_body = json.loads(route.calls[2].request.content)
    assert "tools" not in third_body


@respx.mock
def test_grounded_success_keeps_marker_and_does_not_set_memo():
    route = respx.post(ENDPOINT).mock(return_value=httpx.Response(200, json=_OK_BODY))
    result = GeminiProvider(api_key="k").generate("Best CRM?")

    assert result.model == f"{MODEL}:grounded"
    assert GeminiProvider._grounding_disabled is False
    assert route.call_count == 1


@respx.mock
def test_503_then_success_retries_same_request():
    route = respx.post(ENDPOINT).mock(
        side_effect=[
            httpx.Response(503, json={"error": {"status": "UNAVAILABLE"}}),
            httpx.Response(200, json=_OK_BODY),
        ]
    )
    result = GeminiProvider(api_key="k").generate("Who sells robots?")

    assert "Acme" in result.text
    assert result.model == f"{MODEL}:grounded"
    assert route.call_count == 2
    # Both attempts carry the same (grounded) payload.
    assert "tools" in json.loads(route.calls[0].request.content)
    assert "tools" in json.loads(route.calls[1].request.content)


@respx.mock
def test_persistent_503_raises_after_one_retry():
    route = respx.post(ENDPOINT).mock(return_value=httpx.Response(503))
    with pytest.raises(httpx.HTTPStatusError):
        GeminiProvider(api_key="k").generate("boom")
    assert route.call_count == 2


@respx.mock
def test_thoughts_tokens_included_in_cost():
    body = {
        "candidates": [{"content": {"parts": [{"text": "answer"}]}}],
        "usageMetadata": {
            "promptTokenCount": 100,
            "candidatesTokenCount": 20,
            "thoughtsTokenCount": 42,
            "totalTokenCount": 162,
        },
    }
    respx.post(ENDPOINT).mock(return_value=httpx.Response(200, json=body))
    result = GeminiProvider(api_key="k").generate("think about it")

    expected = round(
        100 * INPUT_PRICE_PER_TOKEN + (20 + 42) * OUTPUT_PRICE_PER_TOKEN, 6
    )
    assert result.cost_usd == expected


@respx.mock
def test_timeout_then_success_retries():
    route = respx.post(ENDPOINT).mock(
        side_effect=[
            httpx.TimeoutException("slow"),
            httpx.Response(200, json=_OK_BODY),
        ]
    )
    result = GeminiProvider(api_key="k").generate("Who sells robots?")

    assert "Acme" in result.text
    assert route.call_count == 2


@respx.mock
def test_persistent_timeout_raises_after_one_retry():
    route = respx.post(ENDPOINT).mock(side_effect=httpx.TimeoutException("slow"))
    with pytest.raises(httpx.TimeoutException):
        GeminiProvider(api_key="k").generate("boom")
    assert route.call_count == 2
