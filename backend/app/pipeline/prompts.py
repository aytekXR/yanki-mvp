"""Deterministic prompt generation from a KYC profile (no LLM).

Cycles six categories and fills natural-language templates from the KYC fields,
prioritising the company's specific products and services so the questions read
like real user queries ("Who are the leading BAZNA FPV kamikaze drone
manufacturers in Türkiye?") rather than generic mad-libs. Returns exactly
``count`` prompts, each with non-empty text and a category, and never any
duplicates. Templated prompts are testable and free; LLM prompt generation is on
the roadmap, not the MVP.
"""

from __future__ import annotations

from dataclasses import dataclass

CATEGORIES = [
    "recommendation",
    "makers",
    "comparison",
    "alternatives",
    "best-of",
    "use-case",
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


def _specific_topics(kyc) -> list[str]:
    """Product/service phrases — the specific things the company actually sells."""
    return _clean_list([*kyc.products, *kyc.services])


def _topics(kyc) -> list[str]:
    """Subject phrases, specific-first (products, services, industry, keywords)."""
    pool = _clean_list(
        [*kyc.products, *kyc.services, kyc.industry, *kyc.keywords]
    )
    if not pool:
        pool.append("solutions")
    return pool


def _make(category: str, topic: str, kyc) -> str:
    industry = (kyc.industry or "").strip()
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


def generate_prompts(kyc, count: int) -> list[PromptSpec]:
    if count <= 0:
        return []

    topics = _topics(kyc)
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

    return specs[:count]
