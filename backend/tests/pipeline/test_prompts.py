from __future__ import annotations

import math

import pytest

from app.pipeline.kyc import KYC
from app.pipeline.prompts import CATEGORIES, generate_prompts


@pytest.fixture
def defense_kyc() -> KYC:
    return KYC(
        company="Beyond Technologies",
        industry="Defense technology",
        products=["BAZNA FPV kamikaze drone", "Tayron UGV"],
        services=["ISR systems"],
        locations=["Türkiye"],
        competitors=["Baykar"],
    )


def test_generates_exactly_count(sample_kyc):
    specs = generate_prompts(sample_kyc, 10)
    assert len(specs) == 10


def test_every_prompt_has_text_and_category(sample_kyc):
    for spec in generate_prompts(sample_kyc, 10):
        assert spec.text.strip()
        assert spec.category in CATEGORIES


def test_prompts_are_deduped(sample_kyc):
    texts = [spec.text for spec in generate_prompts(sample_kyc, 12)]
    assert len(texts) == len(set(texts))


def test_categories_are_cycled(sample_kyc):
    specs = generate_prompts(sample_kyc, len(CATEGORIES))
    assert [spec.category for spec in specs] == CATEGORIES


def test_fills_from_sparse_kyc():
    sparse = KYC(company="Solo Co")
    specs = generate_prompts(sparse, 10)
    assert len(specs) == 10
    texts = [spec.text for spec in specs]
    assert len(texts) == len(set(texts))
    assert all(spec.text.strip() for spec in specs)


def test_zero_count_returns_empty(sample_kyc):
    assert generate_prompts(sample_kyc, 0) == []


def test_defense_fixture_reads_naturally(defense_kyc):
    specs = generate_prompts(defense_kyc, 10)
    texts = [spec.text for spec in specs]

    assert len(texts) == 10
    assert len(set(texts)) == 10
    # A specific product name surfaces.
    assert any("BAZNA" in text for text in texts)
    # The product-manufacturer-in-location shape is produced.
    assert any(
        text.startswith("Who are the leading ")
        and "manufacturers in Türkiye?" in text
        for text in texts
    )
    # None of the old broken mad-lib shapes.
    for text in texts:
        assert "best Information Technology available" not in text
        assert "best solutions in" not in text
        assert "providers for" not in text  # old "{industry} providers" phrasing


def test_defense_prompts_reference_products_and_services(defense_kyc):
    specs = generate_prompts(defense_kyc, 10)
    specific = ["BAZNA FPV kamikaze drone", "Tayron UGV", "ISR systems"]
    hits = sum(any(term in spec.text for term in specific) for spec in specs)
    assert hits >= math.ceil(10 / 3)
