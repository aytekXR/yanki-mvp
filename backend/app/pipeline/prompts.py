"""Deterministic prompt generation from a KYC profile (no LLM).

GEO prompts simulate what real users ask AI engines, and real users ask about
product *categories* ("Who are the biggest FPV kamikaze drone manufacturers in
Türkiye?"), not about a vendor's private model names. So topics are split by
role:

* QUESTION TOPICS fill the recommendation/makers/comparison/alternatives/
  best-of/use-case slots. They are category-like phrases only — keywords first,
  then short services, then the leading industry segment. A company's own
  product/model names are NEVER used here (a "leading BAZNA V10 manufacturers"
  question is nonsense: BAZNA V10 is *their* model, not a category).
* PRODUCTS get their own dedicated ``brand-probe`` shapes ("What do you know
  about {product} from {company}?") — genuine questions that also test whether
  engines recognise the product. Brand probes are capped at ~1/4 of the output
  so category questions (the real visibility test) dominate.

The industry is used one segment at a time (the first comma/slash-separated
part, e.g. "Defense Technology", not the whole list), and over-long phrases are
kept out of slots where they read badly. Returns exactly ``count`` prompts, each
with non-empty text and a category, and never any duplicates. Templated prompts
are testable and free; LLM prompt generation is on the roadmap, not the MVP.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# The six "category question" shapes, cycled in this order.
CATEGORIES = [
    "recommendation",
    "makers",
    "comparison",
    "alternatives",
    "best-of",
    "use-case",
]

# Products get their own shape under this (non-cycled) category.
BRAND_PROBE = "brand-probe"

# Longest phrase (in words) allowed as a question topic; longer ones read badly
# stuffed into "alternatives to X for {topic}" and similar slots.
_MAX_TOPIC_WORDS = 5
# Services longer than this are not category-like enough to be question topics.
_MAX_SERVICE_WORDS = 4

# Curious-user questions about a specific product that also probe brand
# recognition; each names both the product and the company.
_BRAND_PROBES = [
    "How does {product} by {company} compare to similar products on the market?",
    "What do you know about {product} from {company}?",
]

# Natural padders (used only when a sparse KYC runs out of distinct templates).
_PADDERS = [
    "Which providers are known for excellent {topic}?",
    "What should buyers look for when choosing {topic}?",
    "Who offers the most reliable {topic} today?",
    "What sets a great {topic} provider apart?",
    "Which brands lead the market for {topic}?",
    "How should someone evaluate different {topic} options?",
]


@dataclass(frozen=True)
class PromptSpec:
    text: str
    category: str


def _clean_list(values) -> list[str]:
    out: list[str] = []
    for value in values:
        cleaned = (value or "").strip()
        if cleaned and cleaned not in out:
            out.append(cleaned)
    return out


def _first_segment(value: str) -> str:
    """The leading comma/slash-separated segment, trimmed.

    "Defense Technology, Unmanned Systems, AI" -> "Defense Technology".
    """
    value = (value or "").strip()
    if not value:
        return ""
    return re.split(r"\s*[,/]\s*", value)[0].strip()


def _word_count(phrase: str) -> int:
    return len(phrase.split())


def _question_topics(kyc) -> list[str]:
    """Category-like subjects for the question slots — never product names.

    Order: keywords first, then short services, then the leading industry
    segment. Over-long phrases are dropped so they never land in a slot where
    they read badly.
    """
    industry = _first_segment(kyc.industry)
    short_services = [s for s in _clean_list(kyc.services) if _word_count(s) <= _MAX_SERVICE_WORDS]
    pool = _clean_list([*kyc.keywords, *short_services, industry])
    pool = [topic for topic in pool if 1 <= _word_count(topic) <= _MAX_TOPIC_WORDS]
    if not pool:
        pool.append("solutions")
    return pool


def _make(category: str, topic: str, kyc) -> str:
    industry = _first_segment(kyc.industry)
    locations = _clean_list(kyc.locations)
    location_phrase = f"in {locations[0]}" if locations else "worldwide"
    competitors = _clean_list(kyc.competitors)
    competitor = competitors[0] if competitors else "the market leaders"

    if category == "makers":
        return f"Who are the leading {topic} manufacturers {location_phrase}?"
    if category == "comparison":
        if industry:
            return f"How do the top {industry} companies compare on {topic}?"
        return f"How do the top companies compare on {topic}?"
    if category == "alternatives":
        return f"What are good alternatives to {competitor} for {topic}?"
    if category == "best-of":
        return f"Which companies are known for the best {topic} {location_phrase}?"
    if category == "use-case":
        return f"Which {topic} would you recommend and why?"
    return f"What are the best {topic} options available today?"  # recommendation


def _question_specs(kyc, topics: list[str], count: int) -> list[PromptSpec]:
    """``count`` unique category-question prompts, cycling CATEGORIES/topics.

    Cycles the six shapes over the topics, then pads with natural variants and
    finally a numbered last resort so any ``count`` is reachable even for a
    single-topic sparse KYC.
    """
    specs: list[PromptSpec] = []
    seen: set[str] = set()

    step = 0
    max_steps = count * len(CATEGORIES) * len(topics) + count
    while len(specs) < count and step < max_steps:
        category = CATEGORIES[step % len(CATEGORIES)]
        topic = topics[step % len(topics)]
        text = _make(category, topic, kyc)
        if text not in seen:
            seen.add(text)
            specs.append(PromptSpec(text=text, category=category))
        step += 1

    # Sparse KYC can run out of distinct templates: pad with natural variants
    # (still real English, still cycling categories).
    pad = 0
    max_pad = len(_PADDERS) * len(topics) + count
    while len(specs) < count and pad < max_pad:
        topic = topics[pad % len(topics)]
        text = _PADDERS[pad % len(_PADDERS)].format(topic=topic)
        pad += 1
        if text not in seen:
            seen.add(text)
            category = CATEGORIES[len(specs) % len(CATEGORIES)]
            specs.append(PromptSpec(text=text, category=category))

    # Absolute last resort (single-topic sparse KYC, very high count): numbered
    # but still natural.
    variant = 1
    while len(specs) < count:
        text = f"What are the best {topics[0]} options worth considering ({variant})?"
        variant += 1
        if text not in seen:
            seen.add(text)
            category = CATEGORIES[len(specs) % len(CATEGORIES)]
            specs.append(PromptSpec(text=text, category=category))

    return specs


def _brand_positions(budget: int, count: int) -> set[int]:
    """Spread ``budget`` brand-probe slots evenly across ``count`` positions."""
    if budget <= 0:
        return set()
    return {(i + 1) * count // (budget + 1) for i in range(budget)}


def generate_prompts(kyc, count: int) -> list[PromptSpec]:
    if count <= 0:
        return []

    company = (kyc.company or "").strip()
    topics = _question_topics(kyc)
    products = _clean_list(kyc.products) if company else []

    # Brand probes are a minority: at most ~1/4 of prompts, never more than the
    # products we actually have.
    budget = min(len(products), count // 4)
    brand_positions = _brand_positions(budget, count)

    # More than enough unique category questions to fill every non-brand slot.
    questions = _question_specs(kyc, topics, count)

    specs: list[PromptSpec] = []
    seen: set[str] = set()
    q_index = 0
    p_index = 0

    for pos in range(count):
        spec: PromptSpec | None = None
        if pos in brand_positions and p_index < len(products):
            product = products[p_index]
            shape = _BRAND_PROBES[p_index % len(_BRAND_PROBES)]
            text = shape.format(product=product, company=company)
            p_index += 1
            if text not in seen:
                spec = PromptSpec(text=text, category=BRAND_PROBE)
        if spec is None:
            while q_index < len(questions) and questions[q_index].text in seen:
                q_index += 1
            spec = questions[q_index]
            q_index += 1
        seen.add(spec.text)
        specs.append(spec)

    return specs[:count]
