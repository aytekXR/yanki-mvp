"""The GEO score: a pure function of footprints over total responses (ADR-11)."""

from __future__ import annotations


def geo_score(footprints: int, total: int) -> float:
    """Return ``footprints / total``; ``0.0`` when ``total`` is 0."""
    if total <= 0:
        return 0.0
    return footprints / total
