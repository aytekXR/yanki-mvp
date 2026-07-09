"""API route tests (FastAPI TestClient, in-process, SQLite-backed)."""

import uuid

from app.db.models import Analysis


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
