"""Step 2 - KYC: turn discovered site text into a structured company profile.

Makes one LLM call asking for strict JSON, parses it tolerantly (stripping any
```json fences), and validates against the ``KYC`` model. Aliases always include
the company name and the registrable domain name (without TLD) so footprint
detection has something to match on.

When the model reports no locations, we fall back to the country implied by the
URL's country-code TLD (``.com.tr`` -> Türkiye, ``.de`` -> Germany, ...). That
is a fact about the domain, not a guess about the text, so prompts can still ask
"in Türkiye" instead of "worldwide". A non-empty ``locations`` is never
overridden, and the JSON contract/fields are unchanged.
"""

from __future__ import annotations

import json
from urllib.parse import urlparse

from pydantic import BaseModel, Field, ValidationError

from app.pipeline.errors import PipelineError


class KYC(BaseModel):
    company: str
    description: str = ""
    industry: str = ""
    aliases: list[str] = Field(default_factory=list)
    products: list[str] = Field(default_factory=list)
    services: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    competitors: list[str] = Field(default_factory=list)


_PROMPT = """You are analysing a company from its website text.

Return a single JSON object describing the company, with these fields:
company (string), description (string), industry (string),
aliases (array of strings), products (array of strings),
services (array of strings), keywords (array of strings),
locations (array of strings), competitors (array of strings).

Rules:
- Use ONLY facts stated in the website text. Do NOT guess, infer, or invent
  anything. Prefer an empty string or empty array over a guess.
- Extract SPECIFIC product and model names exactly as written (the actual
  product or model name, never a generic category).
- If the text is in another language (for example Turkish), still write the
  fields in English, but keep proper nouns and product/model names verbatim.
- List competitors ONLY if they are literally named in the text.

Respond with ONLY the JSON object - no prose, no markdown fences.

Website URL: {url}
Website text:
{text}
"""


def build_prompt(text: str, url: str) -> str:
    return _PROMPT.format(url=url, text=text)


def _strip_fences(raw: str) -> str:
    stripped = raw.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


# Second-level labels that are part of a public suffix, not a registrable name
# (e.g. the "co" in example.co.uk, the "com" in example.com.tr). When one of
# these is the second-to-last label we skip it, so ".co.uk"/".com.tr" domains
# yield the real brand (e.g. "globex") rather than a garbage "co"/"com" alias.
_SECOND_LEVEL_SUFFIXES = {"co", "com", "org", "net", "gov", "edu", "ac", "gob", "mil"}


def _registrable_name(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc or parsed.path
    host = host.split("@")[-1].split(":")[0]
    if host.startswith("www."):
        host = host[4:]
    labels = [label for label in host.split(".") if label]
    if len(labels) >= 3 and labels[-2] in _SECOND_LEVEL_SUFFIXES:
        return labels[-3]
    if len(labels) >= 2:
        return labels[-2]
    return labels[0] if labels else ""


# Country-code TLDs we map to a country name for the location fallback. The
# ccTLD is always the final label, so two-level suffixes (com.tr, co.uk) are
# handled for free by looking at that last label.
_CCTLD_COUNTRIES = {
    "tr": "Türkiye",
    "de": "Germany",
    "fr": "France",
    "it": "Italy",
    "es": "Spain",
    "nl": "Netherlands",
    "uk": "United Kingdom",
    "us": "United States",
    "sa": "Saudi Arabia",
    "ae": "United Arab Emirates",
}


def _cctld_country(url: str) -> str:
    """Country name implied by the URL's country-code TLD, or "" if none."""
    parsed = urlparse(url)
    host = parsed.netloc or parsed.path
    host = host.split("@")[-1].split(":")[0]
    labels = [label for label in host.split(".") if label]
    if not labels:
        return ""
    return _CCTLD_COUNTRIES.get(labels[-1].lower(), "")


def _ensure_alias(kyc: KYC, value: str) -> None:
    value = (value or "").strip()
    if value and value.lower() not in [alias.lower() for alias in kyc.aliases]:
        kyc.aliases.append(value)


def generate_kyc(text: str, url: str, provider) -> KYC:
    result = provider.generate(build_prompt(text, url))
    payload = _strip_fences(result.text)
    try:
        data = json.loads(payload)
    except (json.JSONDecodeError, ValueError) as exc:
        raise PipelineError("could not read the company profile") from exc
    if not isinstance(data, dict):
        raise PipelineError("could not read the company profile")
    try:
        kyc = KYC(**data)
    except ValidationError as exc:
        raise PipelineError("the company profile was incomplete") from exc

    _ensure_alias(kyc, kyc.company)
    _ensure_alias(kyc, _registrable_name(url))

    # Deterministic location fallback from the domain's ccTLD (never overrides a
    # location the model actually found).
    if not kyc.locations:
        country = _cctld_country(url)
        if country:
            kyc.locations = [country]

    return kyc
