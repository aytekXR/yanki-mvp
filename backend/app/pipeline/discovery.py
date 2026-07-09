"""Step 1 - discovery: fetch and extract the main text of a company website.

Fetches the homepage plus up to five same-domain links (httpx, 15s timeout,
``YankiBot/0.1`` user agent), strips script/style/nav, and caps the combined
text at ~20k characters. An unreachable or empty site raises ``PipelineError``.
"""

from __future__ import annotations

from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.pipeline.errors import PipelineError

USER_AGENT = "YankiBot/0.1"
TIMEOUT_SECONDS = 15.0
MAX_LINKS = 5
MAX_CHARS = 20_000


def _clean_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "noscript"]):
        tag.decompose()
    return " ".join(soup.get_text(separator=" ", strip=True).split())


def _same_domain(base: str, link: str) -> bool:
    return urlparse(base).netloc == urlparse(link).netloc


def _fetch(client: httpx.Client, url: str) -> str | None:
    try:
        response = client.get(url)
    except httpx.HTTPError:
        return None
    if response.status_code != 200:
        return None
    return response.text


def _same_domain_links(base: str, home_html: str) -> list[str]:
    soup = BeautifulSoup(home_html, "html.parser")
    links: list[str] = []
    for anchor in soup.find_all("a", href=True):
        link = urljoin(base, anchor["href"])
        if (
            link.startswith("http")
            and _same_domain(base, link)
            and link != base
            and link not in links
        ):
            links.append(link)
        if len(links) >= MAX_LINKS:
            break
    return links


def discover(url: str) -> str:
    headers = {"User-Agent": USER_AGENT}
    parts: list[str] = []
    with httpx.Client(
        timeout=TIMEOUT_SECONDS, headers=headers, follow_redirects=True
    ) as client:
        home_html = _fetch(client, url)
        if home_html is None:
            raise PipelineError("could not read the site")
        parts.append(_clean_text(home_html))

        for link in _same_domain_links(url, home_html):
            if sum(len(part) for part in parts) >= MAX_CHARS:
                break
            page_html = _fetch(client, link)
            if page_html:
                parts.append(_clean_text(page_html))

    combined = " ".join(part for part in parts if part).strip()
    if not combined:
        raise PipelineError("could not read the site")
    return combined[:MAX_CHARS]
