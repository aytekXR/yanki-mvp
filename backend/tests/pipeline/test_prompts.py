from __future__ import annotations

from app.pipeline.kyc import KYC
from app.pipeline.prompts import CATEGORIES, generate_prompts


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
