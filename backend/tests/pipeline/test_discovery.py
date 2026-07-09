from __future__ import annotations

import httpx
import pytest
import respx

from app.pipeline.discovery import MAX_CHARS, discover
from app.pipeline.errors import PipelineError

HOME = "https://example.com"


@respx.mock
def test_reachable_site_returns_non_empty_text():
    respx.get(HOME).mock(
        return_value=httpx.Response(
            200, html="<html><body><h1>Acme</h1><p>We build robots.</p></body></html>"
        )
    )
    text = discover(HOME)
    assert "Acme" in text
    assert "robots" in text


@respx.mock
def test_script_and_nav_are_stripped():
    html = (
        "<html><body>"
        "<nav>Home About Contact</nav>"
        "<script>var x = 1;</script>"
        "<p>Real content here.</p>"
        "</body></html>"
    )
    respx.get(HOME).mock(return_value=httpx.Response(200, html=html))
    text = discover(HOME)
    assert "Real content here." in text
    assert "var x" not in text
    assert "Contact" not in text


@respx.mock
def test_unreachable_site_raises_pipeline_error():
    respx.get(HOME).mock(return_value=httpx.Response(404))
    with pytest.raises(PipelineError):
        discover(HOME)


@respx.mock
def test_connection_error_raises_pipeline_error():
    respx.get(HOME).mock(side_effect=httpx.ConnectError("boom"))
    with pytest.raises(PipelineError):
        discover(HOME)


@respx.mock
def test_follows_same_domain_links():
    home = "https://example.com/"  # explicit root path so it only matches "/"
    home_html = (
        '<html><body><p>Home page.</p>'
        '<a href="/about">About</a>'
        '<a href="https://other.com/x">External</a>'
        "</body></html>"
    )
    respx.get(home).mock(return_value=httpx.Response(200, html=home_html))
    about = respx.get("https://example.com/about").mock(
        return_value=httpx.Response(200, html="<p>About us content.</p>")
    )
    external = respx.get("https://other.com/x").mock(
        return_value=httpx.Response(200, html="<p>should not fetch</p>")
    )
    text = discover(home)
    assert "Home page." in text
    assert "About us content." in text
    assert about.called
    assert not external.called  # only same-domain links are followed


@respx.mock
def test_caps_text_length():
    big = "word " * 10_000  # ~50k chars
    respx.get(HOME).mock(
        return_value=httpx.Response(200, html=f"<html><body><p>{big}</p></body></html>")
    )
    text = discover(HOME)
    assert len(text) == MAX_CHARS
