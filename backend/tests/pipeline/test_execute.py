from __future__ import annotations

from sqlalchemy import select

from app.providers.base import ProviderResult
from app.providers.mock import MockProvider


class SpyProvider:
    """Wraps the mock so we can count how many times generate() is called."""

    model = "spy"

    def __init__(self, engine: str, cost: float = 0.01) -> None:
        self.name = engine
        self.calls = 0
        self._cost = cost
        self._inner = MockProvider(engine)

    def generate(self, prompt: str) -> ProviderResult:
        self.calls += 1
        result = self._inner.generate(prompt)
        return ProviderResult(text=result.text, model=self.model, cost_usd=self._cost)


def test_one_response_per_prompt_per_engine(db_session, models, seeded_analysis, settings):
    from app.pipeline import execute

    analysis, prompts = seeded_analysis
    providers = [SpyProvider("a"), SpyProvider("b")]
    written = execute.run_execute(db_session, analysis.id, prompts, providers, settings)

    assert written == len(prompts) * len(providers)
    rows = db_session.execute(select(models.Response)).scalars().all()
    assert len(rows) == len(prompts) * len(providers)
    assert {row.engine for row in rows} == {"a", "b"}


def test_cache_consulted_before_provider_on_second_run(
    db_session, models, seeded_analysis, settings
):
    from app.pipeline import execute

    analysis, prompts = seeded_analysis
    provider = SpyProvider("a")

    execute.run_execute(db_session, analysis.id, prompts, [provider], settings)
    calls_after_first = provider.calls
    assert calls_after_first == len(prompts)  # one call per prompt (all misses)

    execute.run_execute(db_session, analysis.id, prompts, [provider], settings)
    assert provider.calls == calls_after_first  # every prompt now a cache hit

    rows = db_session.execute(select(models.Response)).scalars().all()
    assert len(rows) == len(prompts) * 2
    cache_rows = db_session.execute(select(models.LlmCache)).scalars().all()
    assert len(cache_rows) == len(prompts)  # one cache entry per unique key


def test_cache_hit_costs_zero(db_session, models, seeded_analysis, settings):
    from app.pipeline import execute

    analysis, prompts = seeded_analysis
    provider = SpyProvider("a", cost=0.01)

    execute.run_execute(db_session, analysis.id, prompts, [provider], settings)
    execute.run_execute(db_session, analysis.id, prompts, [provider], settings)

    rows = db_session.execute(
        select(models.Response).order_by(models.Response.created_at)
    ).scalars().all()
    costs = [float(row.cost_usd) for row in rows]
    assert costs[: len(prompts)] == [0.01] * len(prompts)  # first run paid
    assert costs[len(prompts) :] == [0.0] * len(prompts)  # cache hits free


def test_max_responses_per_job_is_enforced(
    db_session, models, seeded_analysis, settings
):
    from app.pipeline import execute

    analysis, prompts = seeded_analysis  # 3 prompts
    settings.max_responses_per_job = 2
    providers = [SpyProvider("a"), SpyProvider("b")]

    written = execute.run_execute(db_session, analysis.id, prompts, providers, settings)
    assert written == 2
    rows = db_session.execute(select(models.Response)).scalars().all()
    assert len(rows) == 2
