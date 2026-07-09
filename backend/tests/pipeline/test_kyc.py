from __future__ import annotations

import pytest

from app.pipeline.errors import PipelineError
from app.pipeline.kyc import KYC, generate_kyc
from app.providers.base import ProviderResult


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


def test_invalid_json_raises_pipeline_error():
    with pytest.raises(PipelineError):
        generate_kyc("text", "https://x.com", _CannedProvider("not json at all"))


def test_missing_required_field_raises_pipeline_error():
    # No "company" field -> validation failure -> PipelineError.
    raw = '{"description": "d", "industry": "i"}'
    with pytest.raises(PipelineError):
        generate_kyc("text", "https://x.com", _CannedProvider(raw))
