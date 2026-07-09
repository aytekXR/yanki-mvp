"""Pick which providers to use, honouring DRY_RUN and PANEL_ENGINES.

``get_panel`` returns the list of engines each prompt is run against; when
``DRY_RUN`` is on they are all deterministic mocks. ``get_analysis_provider``
returns the single provider used for the KYC call.
"""

from __future__ import annotations

from app.providers.base import Provider
from app.providers.mock import MockProvider

DEFAULT_PANEL = ["anthropic", "openai", "gemini", "perplexity"]


def _panel_engines(settings) -> list[str]:
    raw = getattr(settings, "panel_engines", None) or ",".join(DEFAULT_PANEL)
    return [engine.strip() for engine in raw.split(",") if engine.strip()]


def _build_real(engine: str, settings) -> Provider:
    if engine == "anthropic":
        from app.providers.anthropic_provider import AnthropicProvider

        return AnthropicProvider(api_key=getattr(settings, "anthropic_api_key", ""))
    if engine == "openai":
        from app.providers.openai_provider import OpenAIProvider

        return OpenAIProvider(api_key=getattr(settings, "openai_api_key", ""))
    if engine == "gemini":
        from app.providers.gemini_provider import GeminiProvider

        return GeminiProvider()
    if engine == "perplexity":
        from app.providers.perplexity_provider import PerplexityProvider

        return PerplexityProvider()
    # Unknown engine name → fall back to a mock so the pipeline never crashes.
    return MockProvider(engine)


def get_panel(settings) -> list[Provider]:
    engines = _panel_engines(settings)
    if getattr(settings, "dry_run", True):
        return [MockProvider(engine) for engine in engines]
    return [_build_real(engine, settings) for engine in engines]


def get_analysis_provider(settings) -> Provider:
    if getattr(settings, "dry_run", True):
        return MockProvider("mock")
    engines = _panel_engines(settings)
    kyc_engine = engines[0] if engines else "anthropic"
    return _build_real(kyc_engine, settings)
