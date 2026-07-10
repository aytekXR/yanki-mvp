"""The fixed, versioned checker prompt set: 12 / unique / stable / tagged."""

from __future__ import annotations

from app.pipeline import checker_prompts
from app.pipeline.kyc import KYC
from app.pipeline.prompts import PromptSpec

# The category tags the checker set is allowed to emit (shared vocabulary with
# prompts.CATEGORIES). A tag outside this set is a wording bug.
_ALLOWED_CATEGORIES = {
    "recommendation",
    "makers",
    "comparison",
    "alternatives",
    "best-of",
    "use-case",
}


def test_generate_returns_exactly_twelve(sample_kyc):
    specs = checker_prompts.generate(sample_kyc, "en")
    assert len(specs) == 12


def test_all_prompts_non_empty(sample_kyc):
    specs = checker_prompts.generate(sample_kyc, "en")
    assert all(isinstance(s, PromptSpec) for s in specs)
    assert all(s.text.strip() for s in specs)


def test_all_prompts_unique(sample_kyc):
    specs = checker_prompts.generate(sample_kyc, "en")
    assert len({s.text for s in specs}) == 12


def test_every_prompt_is_category_tagged(sample_kyc):
    specs = checker_prompts.generate(sample_kyc, "en")
    for spec in specs:
        assert spec.category in _ALLOWED_CATEGORIES


def test_prompts_are_byte_stable_across_runs(sample_kyc):
    first = checker_prompts.generate(sample_kyc, "en")
    second = checker_prompts.generate(sample_kyc, "en")
    assert [(s.text, s.category) for s in first] == [(s.text, s.category) for s in second]


def test_version_constant_is_stamped():
    assert checker_prompts.VERSION == "checker-en-v1"


def test_unwired_lang_falls_back_to_english(sample_kyc):
    # 'tr' is a legal submit today but has no wired set yet (P5.8); it must fall
    # back to English rather than fail — never crash, never return an empty set.
    en = checker_prompts.generate(sample_kyc, "en")
    tr = checker_prompts.generate(sample_kyc, "tr")
    assert [(s.text, s.category) for s in tr] == [(s.text, s.category) for s in en]


def test_sparse_kyc_still_yields_twelve_unique_non_empty():
    # Every optional field empty: the deterministic fallbacks (topic 'solutions',
    # 'worldwide', 'the market leaders') must still produce 12 unique prompts.
    sparse = KYC(company="OnlyName")
    specs = checker_prompts.generate(sparse, "en")
    assert len(specs) == 12
    assert len({s.text for s in specs}) == 12
    assert all(s.text.strip() for s in specs)


def test_prompts_use_category_topic_not_brand_name(sample_kyc):
    # The checker measures unprompted visibility, so the brand name must NOT
    # appear in any question — it is searched for in the answers instead.
    specs = checker_prompts.generate(sample_kyc, "en")
    assert all(sample_kyc.company.lower() not in s.text.lower() for s in specs)
