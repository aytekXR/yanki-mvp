"""Binary footprint detection: does the company appear in a raw answer?

Pure, deterministic, case-insensitive string matching over the company name,
its aliases (which include the registrable domain name) — no LLM. On a hit it
returns a short snippet of context around the first match.
"""

from __future__ import annotations

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

    haystack = raw_text.lower()
    best_index: int | None = None
    best_len = 0
    for term in _terms(kyc):
        index = haystack.find(term.lower())
        if index != -1 and (best_index is None or index < best_index):
            best_index = index
            best_len = len(term)

    if best_index is None:
        return False, None

    start = max(0, best_index - _SNIPPET_RADIUS)
    end = min(len(raw_text), best_index + best_len + _SNIPPET_RADIUS)
    return True, raw_text[start:end]
