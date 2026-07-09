"""Deterministic prompt generation from a KYC profile (no LLM).

Cycles five categories and fills templates from the KYC fields. Returns exactly
``count`` prompts, each with non-empty text and a category, and never any
duplicates. Templated prompts are testable and free; LLM prompt generation is on
the roadmap, not the MVP.
"""

from __future__ import annotations

from dataclasses import dataclass

CATEGORIES = ["recommendation", "comparison", "alternatives", "best-of", "use-case"]


@dataclass(frozen=True)
class PromptSpec:
    text: str
    category: str


def _topics(kyc) -> list[str]:
    """Subject phrases pulled from the KYC profile, with a safe fallback."""
    pool: list[str] = []
    for value in [kyc.industry, *kyc.products, *kyc.keywords, *kyc.services]:
        cleaned = (value or "").strip()
        if cleaned and cleaned not in pool:
            pool.append(cleaned)
    if not pool:
        pool.append("solutions")
    return pool


def _make(category: str, topic: str, kyc) -> str:
    industry = (kyc.industry or "").strip() or "companies"
    location = (kyc.locations[0].strip() if kyc.locations else "") or "the market"
    competitor = (
        (kyc.competitors[0].strip() if kyc.competitors else "")
        or f"{industry} providers"
    )
    if category == "comparison":
        return f"How do the leading {industry} providers compare for {topic}?"
    if category == "alternatives":
        return f"What are the best alternatives to {competitor} for {topic}?"
    if category == "best-of":
        return f"What is the best {topic} in {location}?"
    if category == "use-case":
        return f"Which {industry} solution works best for {topic}?"
    return f"What are the best {topic} available today?"  # recommendation


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

    # Sparse KYC can run out of distinct templates; pad with numbered variants.
    variant = 1
    while len(specs) < count:
        category = CATEGORIES[len(specs) % len(CATEGORIES)]
        text = f"What are the best {topics[0]} options to consider (list {variant})?"
        variant += 1
        if text not in seen:
            seen.add(text)
            specs.append(PromptSpec(text=text, category=category))

    return specs[:count]
