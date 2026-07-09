"""Binary footprint detection: does the company appear in a raw answer?

Pure, deterministic, case-insensitive matching over the company name and its
aliases (which include the registrable domain name) — no LLM. Terms are matched
on word boundaries (``\\b``), not raw substrings, so a short term like ``GE`` or
``Co`` never counts as a hit inside an unrelated word (``general``, ``compare``).
On a hit it returns a short snippet of context around the first match.
"""

from __future__ import annotations

import re

_SNIPPET_RADIUS = 60
_MIN_TERM_LEN = 2


def _terms(kyc) -> list[str]:
    """Distinct, non-trivial search terms drawn from the KYC profile."""
    seen: list[str] = []
    lowered: set[str] = set()
    for value in [kyc.company, *kyc.aliases]:
        term = (value or "").strip()
        if len(term) >= _MIN_TERM_LEN and term.lower() not in lowered:
            seen.append(term)
            lowered.add(term.lower())
    return seen


def detect(raw_text: str, kyc) -> tuple[bool, str | None]:
    """Return ``(True, snippet)`` if the company appears, else ``(False, None)``."""
    if not raw_text:
        return False, None

    best_index: int | None = None
    best_len = 0
    for term in _terms(kyc):
        # Match on word boundaries so a short term never hits inside a longer
        # word (e.g. "Co" must not match "compare"/"companies").
        pattern = re.compile(r"\b" + re.escape(term) + r"\b", re.IGNORECASE)
        match = pattern.search(raw_text)
        if match and (best_index is None or match.start() < best_index):
            best_index = match.start()
            best_len = match.end() - match.start()

    if best_index is None:
        return False, None

    start = max(0, best_index - _SNIPPET_RADIUS)
    end = min(len(raw_text), best_index + best_len + _SNIPPET_RADIUS)
    return True, raw_text[start:end]
