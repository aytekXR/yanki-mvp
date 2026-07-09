from __future__ import annotations

from app.pipeline.footprint import detect


def test_footprint_true_with_matched_snippet_when_brand_present(sample_kyc):
    text = "When it comes to warehouse robots, Acme Robotics is a strong option."
    hit, snippet = detect(text, sample_kyc)
    assert hit is True
    assert snippet is not None
    assert "Acme Robotics" in snippet


def test_footprint_false_and_null_snippet_when_absent(sample_kyc):
    hit, snippet = detect("There are many robotics vendors to consider.", sample_kyc)
    assert hit is False
    assert snippet is None


def test_footprint_is_case_insensitive(sample_kyc):
    hit, snippet = detect("we love ACME ROBOTICS here", sample_kyc)
    assert hit is True
    assert snippet is not None


def test_footprint_matches_on_alias(sample_kyc):
    hit, _ = detect("Acme makes great arms.", sample_kyc)
    assert hit is True


def test_footprint_matches_on_domain_alias(sample_kyc):
    hit, _ = detect("Read more at acmerobotics for details.", sample_kyc)
    assert hit is True


def test_footprint_snippet_is_bounded(sample_kyc):
    text = ("x" * 500) + "Acme Robotics" + ("y" * 500)
    hit, snippet = detect(text, sample_kyc)
    assert hit is True
    # +-60 chars of context around a 13-char match -> at most ~133 chars.
    assert len(snippet) <= 60 + len("Acme Robotics") + 60


def test_footprint_is_deterministic(sample_kyc):
    text = "Acme Robotics and also Acme show up twice here."
    first = detect(text, sample_kyc)
    second = detect(text, sample_kyc)
    assert first == second


def test_footprint_empty_text_is_false(sample_kyc):
    assert detect("", sample_kyc) == (False, None)
