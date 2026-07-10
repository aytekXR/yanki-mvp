"""POST /api/v1/waitlist tests (P5.13).

Covers: a valid signup 202s and records one normalized row; a malformed email is
a 4xx (never 500); a duplicate email 202s but fires the emails only ONCE (the
new-signup detection is by the RETURNING row, no enumeration); the per-IP hourly
rate limit rejects with 429 + Retry-After.
"""

from __future__ import annotations

import app.api.routes as routes
from app.db.models import WaitlistSignup


def _record_emails(monkeypatch):
    """Replace the route's email fan-out with a call recorder. Returns the list of
    (email, total) tuples it was invoked with."""
    calls: list[tuple[str, int]] = []
    monkeypatch.setattr(
        routes, "send_waitlist_emails", lambda email, total, settings: calls.append((email, total))
    )
    return calls


def test_valid_signup_returns_202_and_records_one_normalized_row(client, db_session, monkeypatch):
    calls = _record_emails(monkeypatch)

    resp = client.post("/api/v1/waitlist", json={"email": "  Joiner@Example.COM "})
    assert resp.status_code == 202
    assert resp.json() == {"ok": True}

    rows = db_session.query(WaitlistSignup).all()
    assert len(rows) == 1
    assert rows[0].email == "joiner@example.com"  # trimmed + lowercased
    # Emails fired once, with the normalized address and a count of 1.
    assert calls == [("joiner@example.com", 1)]


def test_malformed_email_returns_422_and_records_nothing(client, db_session, monkeypatch):
    calls = _record_emails(monkeypatch)

    for bad in ("not-an-email", "no@tld", "", "a@b@c.com"):
        resp = client.post("/api/v1/waitlist", json={"email": bad})
        assert resp.status_code == 422, bad
    resp = client.post("/api/v1/waitlist", json={})  # missing field
    assert resp.status_code == 422

    assert db_session.query(WaitlistSignup).count() == 0
    assert calls == []  # no emails on a rejected submit


def test_duplicate_email_still_202s_but_emails_fire_only_once(client, db_session, monkeypatch):
    calls = _record_emails(monkeypatch)

    first = client.post("/api/v1/waitlist", json={"email": "dup@example.com"})
    assert first.status_code == 202
    # A case/whitespace variant of the same address is the SAME normalized email.
    second = client.post("/api/v1/waitlist", json={"email": " DUP@example.com "})
    assert second.status_code == 202  # no enumeration — duplicate looks identical

    assert db_session.query(WaitlistSignup).count() == 1  # ON CONFLICT DO NOTHING
    assert calls == [("dup@example.com", 1)]  # emails sent only for the NEW signup


def test_per_ip_rate_limit_returns_429_with_retry_after(client, db_session, monkeypatch):
    _record_emails(monkeypatch)
    monkeypatch.setattr(routes, "WAITLIST_RATE_LIMIT_PER_IP_HOUR", 2)
    ip = "203.0.113.55"
    headers = {"X-Forwarded-For": ip}

    for i in range(2):
        resp = client.post("/api/v1/waitlist", json={"email": f"a{i}@example.com"}, headers=headers)
        assert resp.status_code == 202

    blocked = client.post("/api/v1/waitlist", json={"email": "a2@example.com"}, headers=headers)
    assert blocked.status_code == 429
    assert 1 <= int(blocked.headers["Retry-After"]) <= 3600
    # The throttled submit recorded no row.
    assert db_session.query(WaitlistSignup).count() == 2
