"""API route tests (FastAPI TestClient, in-process, SQLite-backed)."""

import uuid
from decimal import Decimal

from app.db.models import Analysis, Prompt, Response


def test_submit_valid_url_returns_202_and_queued_row(client, db_session):
    resp = client.post("/api/v1/analyses", json={"url": "https://example.com"})

    assert resp.status_code == 202
    body = resp.json()
    assert "id" in body

    analysis = db_session.get(Analysis, uuid.UUID(body["id"]))
    assert analysis is not None
    assert analysis.status == "queued"
    assert analysis.progress == 0


def test_submit_invalid_url_returns_422(client):
    resp = client.post("/api/v1/analyses", json={"url": "not-a-url"})
    assert resp.status_code == 422


def test_submit_ssrf_target_is_rejected(client, db_session):
    # Loopback / link-local (cloud metadata) hosts must not be accepted for the
    # worker to fetch — reject them at the boundary.
    for url in (
        "http://127.0.0.1:8000/",
        "http://169.254.169.254/latest/meta-data/",
    ):
        resp = client.post("/api/v1/analyses", json={"url": url})
        assert resp.status_code == 422, url

    # Nothing was enqueued.
    assert db_session.query(Analysis).count() == 0


def test_submit_missing_url_returns_422(client):
    resp = client.post("/api/v1/analyses", json={})
    assert resp.status_code == 422


def test_get_unknown_id_returns_404(client):
    resp = client.get(f"/api/v1/analyses/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_get_returns_envelope_with_result_always_present(client, make_analysis):
    analysis = make_analysis(url="https://acme.test")

    resp = client.get(f"/api/v1/analyses/{analysis.id}")
    assert resp.status_code == 200

    body = resp.json()
    assert body["id"] == str(analysis.id)
    assert body["url"] == "https://acme.test"
    assert body["status"] == "queued"
    assert body["progress"] == 0
    assert body["current_step"] is None
    assert body["error"] is None

    # The result envelope is always present; inner fields are null/empty until produced.
    assert "result" in body
    result = body["result"]
    assert result["kyc"] is None
    assert result["prompts"] == []
    assert result["responses"] == []
    assert result["geo_score"] is None
    assert result["footprint_count"] is None
    assert result["total_responses"] is None


def test_get_done_analysis_serializes_full_result(client, db_session, make_analysis):
    # FR-2 / Results acceptance: a done analysis returns nested KYC, prompts,
    # responses and score, with cost_usd (Numeric) coerced to a float.
    analysis = make_analysis(
        url="https://acme.test",
        status="done",
        progress=100,
        kyc={"company": "Acme", "industry": "Robotics"},
        geo_score=0.5,
        footprint_count=1,
        total_responses=2,
    )
    prompt = Prompt(
        analysis_id=analysis.id, text="Best warehouse robots?", category="recommendation"
    )
    db_session.add(prompt)
    db_session.flush()
    db_session.add_all(
        [
            Response(
                analysis_id=analysis.id,
                prompt_id=prompt.id,
                engine="anthropic",
                model="claude",
                raw_text="Acme is a strong option.",
                footprint=True,
                matched_snippet="Acme is a strong option.",
                cost_usd=Decimal("0.001234"),
            ),
            Response(
                analysis_id=analysis.id,
                prompt_id=prompt.id,
                engine="openai",
                model="gpt",
                raw_text="Plenty of vendors exist.",
                footprint=False,
                matched_snippet=None,
                cost_usd=Decimal("0"),
            ),
        ]
    )
    db_session.commit()

    resp = client.get(f"/api/v1/analyses/{analysis.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "done"

    result = body["result"]
    assert result["kyc"] == {"company": "Acme", "industry": "Robotics"}
    assert result["geo_score"] == 0.5
    assert result["footprint_count"] == 1
    assert result["total_responses"] == 2

    assert len(result["prompts"]) == 1
    assert result["prompts"][0]["id"] == str(prompt.id)
    assert result["prompts"][0]["text"] == "Best warehouse robots?"
    assert result["prompts"][0]["category"] == "recommendation"

    assert len(result["responses"]) == 2
    hit = next(r for r in result["responses"] if r["engine"] == "anthropic")
    assert hit["prompt_id"] == str(prompt.id)
    assert hit["model"] == "claude"
    assert hit["raw_text"] == "Acme is a strong option."
    assert hit["footprint"] is True
    assert hit["matched_snippet"] == "Acme is a strong option."
    assert isinstance(hit["cost_usd"], float)
    assert hit["cost_usd"] == 0.001234
