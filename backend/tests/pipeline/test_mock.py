from __future__ import annotations

import hashlib
import json

from app.providers.mock import MOCK_COMPANY, MockProvider


def _mentions_flag(prompt: str) -> bool:
    return hashlib.sha256(prompt.encode("utf-8")).digest()[0] % 2 == 0


def _find_prompt(mentions: bool) -> str:
    for i in range(1000):
        prompt = f"Recommend a tool for task {i}?"
        if _mentions_flag(prompt) == mentions:
            return prompt
    raise AssertionError("no suitable prompt found")


def test_mentions_company_when_hash_is_even():
    prompt = _find_prompt(mentions=True)
    result = MockProvider("anthropic").generate(prompt)
    assert MOCK_COMPANY in result.text
    assert result.cost_usd == 0.0
    assert result.model == "mock"


def test_omits_company_when_hash_is_odd():
    prompt = _find_prompt(mentions=False)
    result = MockProvider("openai").generate(prompt)
    assert MOCK_COMPANY not in result.text
    assert result.cost_usd == 0.0


def test_is_deterministic():
    prompt = "Which CRM should I use?"
    first = MockProvider("gemini").generate(prompt)
    second = MockProvider("gemini").generate(prompt)
    assert first == second


def test_kyc_request_returns_valid_json():
    prompt = "Return a single JSON object describing the company."
    result = MockProvider("mock").generate(prompt)
    data = json.loads(result.text)
    assert data["company"] == MOCK_COMPANY
    assert isinstance(data["aliases"], list)
