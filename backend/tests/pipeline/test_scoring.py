from __future__ import annotations

import pytest

from app.pipeline.scoring import geo_score


def test_geo_score_is_footprints_over_total():
    assert geo_score(9, 20) == pytest.approx(0.45)


def test_geo_score_all_footprints_is_one():
    assert geo_score(5, 5) == 1.0


def test_geo_score_no_footprints_is_zero():
    assert geo_score(0, 10) == 0.0


def test_geo_score_zero_total_does_not_divide_by_zero():
    assert geo_score(0, 0) == 0.0
    # even a nonsensical footprint count stays safe
    assert geo_score(3, 0) == 0.0
