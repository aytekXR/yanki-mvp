from __future__ import annotations

import math

import pytest

from app.pipeline.kyc import KYC, generate_kyc
from app.pipeline.prompts import BRAND_PROBE, CATEGORIES, generate_prompts
from app.providers.base import ProviderResult


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


# The exact real prod KYC for https://beyondtech.com.tr (analysis 58913428),
# with locations left empty as the model returned them.
def _beyondtech_kyc(locations: list[str] | None = None) -> KYC:
    return KYC(
        company="Beyond Technologies",
        industry="Defense Technology, Unmanned Systems, Artificial Intelligence",
        description="A technology company specializing in autonomous systems.",
        aliases=["Beyond Technologies", "beyondtech"],
        products=[
            "BAZNA V7",
            "BAZNA V10",
            "BAZNA V15",
            "BAZNA F",
            "LIFTRON",
            "FEDAİ",
            "TAKTIK İKA",
            "TAKTIK OTONOMI SİSTEMİ — İKA",
            "GÖRÜNTÜ TABANLÜ SEYRÜSEFER SİSTEMİ — İHA",
        ],
        services=[
            "End-to-end development from concept to field integration",
            "Software development",
            "Hardware development",
            "System integration",
        ],
        keywords=[
            "unmanned aerial vehicle",
            "UAV",
            "unmanned ground vehicle",
            "UGV",
            "autonomous systems",
            "tactical kamikaze UAV",
            "fiber optic",
            "EW immune",
            "anti-armor",
            "RPG-7 capability",
            "payload capacity",
            "flight endurance",
            "artificial intelligence",
            "defense",
        ],
        locations=locations or [],
        competitors=[],
    )


class _CannedProvider:
    name = "canned"
    model = "canned"

    def __init__(self, text: str) -> None:
        self._text = text

    def generate(self, prompt: str) -> ProviderResult:
        return ProviderResult(text=self._text, model=self.model, cost_usd=0.0)


def test_generates_exactly_count(sample_kyc):
    specs = generate_prompts(sample_kyc, 10)
    assert len(specs) == 10


def test_every_prompt_has_text_and_category(sample_kyc):
    for spec in generate_prompts(sample_kyc, 10):
        assert spec.text.strip()
        assert spec.category in CATEGORIES or spec.category == BRAND_PROBE


def test_prompts_are_deduped(sample_kyc):
    texts = [spec.text for spec in generate_prompts(sample_kyc, 12)]
    assert len(texts) == len(set(texts))


def test_categories_are_cycled():
    # No products -> no brand probes -> the six category shapes cycle cleanly.
    kyc = KYC(company="Acme", keywords=["automation", "robotics", "logistics"])
    specs = generate_prompts(kyc, len(CATEGORIES))
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


# --- Round 2: the exact real prod KYC (beyondtech.com.tr) -------------------

# Every product/model name; none of these may appear in a category slot.
_BEYONDTECH_PRODUCTS = [
    "BAZNA V7",
    "BAZNA V10",
    "BAZNA V15",
    "BAZNA F",
    "LIFTRON",
    "FEDAİ",
    "TAKTIK İKA",
    "TAKTIK OTONOMI SİSTEMİ — İKA",
    "GÖRÜNTÜ TABANLÜ SEYRÜSEFER SİSTEMİ — İHA",
]


def test_beyondtech_ten_unique_prompts():
    kyc = _beyondtech_kyc(locations=["Türkiye"])
    specs = generate_prompts(kyc, 10)
    texts = [spec.text for spec in specs]
    assert len(texts) == 10
    assert len(set(texts)) == 10


def test_beyondtech_no_product_in_category_slot():
    kyc = _beyondtech_kyc(locations=["Türkiye"])
    specs = generate_prompts(kyc, 10)
    for spec in specs:
        if spec.category == BRAND_PROBE:
            continue
        for product in _BEYONDTECH_PRODUCTS:
            assert product not in spec.text, spec.text
    # The specific broken shapes from the live run must not recur.
    for spec in specs:
        assert "BAZNA V10 manufacturers" not in spec.text
        assert "Which FEDAİ would you recommend" not in spec.text


def test_beyondtech_has_keyword_makers_question():
    kyc = _beyondtech_kyc(locations=["Türkiye"])
    texts = [spec.text for spec in generate_prompts(kyc, 10)]
    assert any(
        "manufacturers" in text
        and any(term in text for term in ("UAV", "unmanned", "kamikaze"))
        for text in texts
    )


def test_beyondtech_brand_probes_are_a_minority_and_well_formed():
    kyc = _beyondtech_kyc(locations=["Türkiye"])
    specs = generate_prompts(kyc, 10)
    probes = [spec for spec in specs if spec.category == BRAND_PROBE]
    assert 1 <= len(probes) <= 3
    for probe in probes:
        assert "Beyond Technologies" in probe.text
        assert any(product in probe.text for product in _BEYONDTECH_PRODUCTS)


def test_beyondtech_industry_uses_first_segment_only():
    kyc = _beyondtech_kyc(locations=["Türkiye"])
    texts = [spec.text for spec in generate_prompts(kyc, 10)]
    full_industry = "Defense Technology, Unmanned Systems, Artificial Intelligence"
    assert all(full_industry not in text for text in texts)
    # Where the industry surfaces it is the trimmed first segment.
    assert any("Defense Technology" in text for text in texts)


def test_beyondtech_cctld_fallback_feeds_location_into_prompts():
    # locations empty, but the .com.tr domain fallback yields Türkiye, so the
    # kyc function + generate_prompts together produce "in Türkiye" prompts.
    raw = _beyondtech_kyc(locations=[]).model_dump_json()
    kyc = generate_kyc("site text", "https://beyondtech.com.tr", _CannedProvider(raw))
    assert kyc.locations == ["Türkiye"]
    texts = [spec.text for spec in generate_prompts(kyc, 10)]
    assert any("in Türkiye" in text for text in texts)
    assert all("worldwide" not in text for text in texts)
