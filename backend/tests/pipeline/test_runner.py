from __future__ import annotations

from sqlalchemy import select


def test_run_pipeline_walks_all_steps_and_scores(db_session, models, settings, monkeypatch):
    from app.pipeline import discovery, runner

    # Avoid real network: hand discovery a canned page.
    monkeypatch.setattr(
        discovery, "discover", lambda url: "Acme builds warehouse robots and tools."
    )

    analysis = models.Analysis(url="https://example.com", status="running")
    db_session.add(analysis)
    db_session.flush()

    result = runner.run_pipeline(db_session, analysis.id, settings)

    # Final status + progress + heartbeat.
    assert result.status == "done"
    assert result.progress == 100
    assert result.current_step is None
    assert result.claimed_at is not None

    # KYC persisted as JSON with a company name.
    assert result.kyc is not None
    assert result.kyc["company"]

    # Prompts persisted (PROMPT_COUNT of them).
    prompts = db_session.execute(
        select(models.Prompt).where(models.Prompt.analysis_id == analysis.id)
    ).scalars().all()
    assert len(prompts) == settings.prompt_count

    # Responses: one per prompt per panel engine (4 engines in DRY_RUN).
    responses = db_session.execute(
        select(models.Response).where(models.Response.analysis_id == analysis.id)
    ).scalars().all()
    assert len(responses) == settings.prompt_count * 4
    assert result.total_responses == len(responses)

    # Footprint recorded on every response; score is consistent with the counts.
    assert all(response.footprint is not None for response in responses)
    hits = sum(1 for response in responses if response.footprint)
    assert result.footprint_count == hits
    assert result.geo_score == (hits / len(responses))
    assert 0.0 <= result.geo_score <= 1.0
