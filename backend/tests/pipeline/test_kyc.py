from __future__ import annotations

import pytest

from app.pipeline.errors import PipelineError
from app.pipeline.kyc import KYC, build_prompt, generate_kyc
from app.providers.base import ProviderResult


def test_prompt_forbids_guessing_and_keeps_mock_coupling():
    prompt = build_prompt("some site text", "https://x.com")
    # Anti-hallucination instruction is present.
    assert "Use ONLY facts stated in the website text" in prompt
    assert "Do NOT guess" in prompt
    # The mock provider keys off this substring (case-insensitive) - keep it.
    assert "json object" in prompt.lower()


class _CannedProvider:
    """A provider that returns a fixed string, ignoring the prompt."""

    name = "canned"
    model = "canned"

    def __init__(self, text: str) -> None:
        self._text = text

    def generate(self, prompt: str) -> ProviderResult:
        return ProviderResult(text=self._text, model=self.model, cost_usd=0.0)


def test_parses_fenced_json_and_validates():
    raw = (
        "```json\n"
        '{"company": "Globex", "description": "Widgets", "industry": "Manufacturing",'
        ' "aliases": ["Globex Corp"], "products": ["Widget"]}\n'
        "```"
    )
    kyc = generate_kyc("site text", "https://globex.com", _CannedProvider(raw))
    assert isinstance(kyc, KYC)
    assert kyc.company == "Globex"
    assert kyc.industry == "Manufacturing"


def test_aliases_always_include_company_and_domain():
    raw = '{"company": "Globex", "description": "d", "industry": "i"}'
    kyc = generate_kyc("text", "https://www.globex.co.uk/about", _CannedProvider(raw))
    lowered = [alias.lower() for alias in kyc.aliases]
    assert "globex" in lowered  # company name (and registrable domain name)


def test_domain_alias_skips_multipart_public_suffix():
    # For a multi-label ccTLD the registrable label is the brand, not the public
    # suffix segment: .co.uk -> "globex" (never "co"), .com.tr -> "sirket"
    # (never "com"). A short "co"/"com" alias would otherwise match inside
    # "companies"/"compare" and wrongly inflate the footprint score.
    raw = '{"company": "Globex", "description": "d", "industry": "i"}'
    couk = generate_kyc("text", "https://www.globex.co.uk/about", _CannedProvider(raw))
    couk_aliases = [alias.lower() for alias in couk.aliases]
    assert "globex" in couk_aliases
    assert "co" not in couk_aliases

    raw2 = '{"company": "Sirket", "description": "d", "industry": "i"}'
    comtr = generate_kyc("text", "https://sirket.com.tr", _CannedProvider(raw2))
    comtr_aliases = [alias.lower() for alias in comtr.aliases]
    assert "sirket" in comtr_aliases
    assert "com" not in comtr_aliases


def test_invalid_json_raises_pipeline_error():
    with pytest.raises(PipelineError):
        generate_kyc("text", "https://x.com", _CannedProvider("not json at all"))


def test_missing_required_field_raises_pipeline_error():
    # No "company" field -> validation failure -> PipelineError.
    raw = '{"description": "d", "industry": "i"}'
    with pytest.raises(PipelineError):
        generate_kyc("text", "https://x.com", _CannedProvider(raw))
