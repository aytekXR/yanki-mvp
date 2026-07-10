from __future__ import annotations

from types import SimpleNamespace

from app.providers import registry
from app.providers.mock import MockProvider


def test_dry_run_panel_is_all_mocks_named_after_engines():
    settings = SimpleNamespace(
        dry_run=True, panel_engines="anthropic,openai,gemini,perplexity"
    )
    panel = registry.get_panel(settings)
    assert len(panel) == 4
    assert all(isinstance(provider, MockProvider) for provider in panel)
    assert [provider.name for provider in panel] == [
        "anthropic",
        "openai",
        "gemini",
        "perplexity",
    ]


def test_dry_run_analysis_provider_is_mock():
    settings = SimpleNamespace(dry_run=True)
    provider = registry.get_analysis_provider(settings)
    assert isinstance(provider, MockProvider)


def test_panel_honours_custom_engine_list():
    settings = SimpleNamespace(dry_run=True, panel_engines="anthropic, gemini")
    panel = registry.get_panel(settings)
    assert [provider.name for provider in panel] == ["anthropic", "gemini"]


def test_non_dry_run_builds_real_engines():
    # gemini/perplexity are now real REST adapters (P5.7). Construction is
    # offline — no key needed to build, no live call until generate() — so this
    # is safe with blank keys and never touches the network.
    settings = SimpleNamespace(
        dry_run=False,
        panel_engines="gemini,perplexity",
        gemini_api_key="",
        perplexity_api_key="",
    )
    panel = registry.get_panel(settings)
    assert [provider.name for provider in panel] == ["gemini", "perplexity"]
    assert [provider.model for provider in panel] == [
        "gemini-flash-lite-latest",
        "sonar",
    ]
    assert all(not isinstance(provider, MockProvider) for provider in panel)
