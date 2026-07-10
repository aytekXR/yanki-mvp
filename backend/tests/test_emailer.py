"""Emailer unit tests (P5.13): the Resend POST is env-gated and fail-open.

Uses respx to intercept the httpx call so nothing ever leaves the process — no
live call to resend.com is made or possible here.
"""

from __future__ import annotations

import httpx
import respx

from app.config import Settings
from app.services.emailer import RESEND_ENDPOINT, send_email

_ON = dict(emails_enabled=True, resend_api_key="re_test_key", email_from="from@yanki.test")


@respx.mock
def test_send_email_success_posts_to_resend_and_returns_true():
    route = respx.post(RESEND_ENDPOINT).mock(return_value=httpx.Response(200, json={"id": "e1"}))
    settings = Settings(**_ON)

    assert send_email("joiner@example.com", "Hi", "body", settings) is True

    assert route.called
    request = route.calls.last.request
    assert request.headers["authorization"] == "Bearer re_test_key"
    body = request.content.decode()
    assert "joiner@example.com" in body
    assert "from@yanki.test" in body


@respx.mock
def test_send_email_swallows_http_500_and_returns_false():
    route = respx.post(RESEND_ENDPOINT).mock(return_value=httpx.Response(500))
    settings = Settings(**_ON)

    # A 500 must be swallowed (no raise) and reported as False.
    assert send_email("joiner@example.com", "Hi", "body", settings) is False
    assert route.called


@respx.mock
def test_send_email_disabled_is_a_noop_and_makes_no_call():
    route = respx.post(RESEND_ENDPOINT).mock(return_value=httpx.Response(200))

    # Disabled (default) — never touches the network.
    assert send_email("joiner@example.com", "Hi", "body", Settings(emails_enabled=False)) is False
    # Enabled but no key — also a no-op.
    assert send_email("joiner@example.com", "Hi", "body", Settings(emails_enabled=True)) is False
    assert not route.called
