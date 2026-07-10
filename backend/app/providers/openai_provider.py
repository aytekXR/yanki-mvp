"""Real OpenAI provider (gpt-5-nano) via the official SDK.

Cost is estimated from the token usage the API reports, using a simple price
table constant. Only ever called when ``DRY_RUN`` is off.

Model choice (operator directive 2026-07-10: "use the cheapest"): gpt-5-nano
is OpenAI's cheapest available model ($0.05/$0.40 per 1M tokens, verified
against the official pricing + deprecations pages 2026-07-10; gpt-4.1-nano is
$0.10/$0.40 and its snapshot retires 2026-10-23; the newer gpt-5.4-nano is
$0.20/$1.25). It is a GPT-5-family reasoning model, hence two quirks below:
``max_completion_tokens`` (it rejects ``max_tokens``) and
``reasoning_effort="minimal"`` (reasoning tokens bill as OUTPUT tokens — the
usage-based cost math stays correct either way, but minimal effort keeps that
spend near zero for these simple consumer-style prompts).
"""

from __future__ import annotations

from app.providers.base import ProviderResult

MODEL = "gpt-5-nano"
MAX_TOKENS = 1024

# gpt-5-nano list price: $0.05 / 1M input tokens, $0.40 / 1M output tokens.
INPUT_PRICE_PER_TOKEN = 0.05 / 1_000_000
OUTPUT_PRICE_PER_TOKEN = 0.40 / 1_000_000


class OpenAIProvider:
    name = "openai"
    model = MODEL

    def __init__(self, api_key: str) -> None:
        # Imported lazily so DRY_RUN runs never need the SDK installed at import.
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)

    def generate(self, prompt: str) -> ProviderResult:
        completion = self._client.chat.completions.create(
            model=self.model,
            max_completion_tokens=MAX_TOKENS,
            reasoning_effort="minimal",
            messages=[{"role": "user", "content": prompt}],
        )
        text = completion.choices[0].message.content or ""
        usage = completion.usage
        prompt_tokens = usage.prompt_tokens if usage else 0
        completion_tokens = usage.completion_tokens if usage else 0
        cost = (
            prompt_tokens * INPUT_PRICE_PER_TOKEN
            + completion_tokens * OUTPUT_PRICE_PER_TOKEN
        )
        return ProviderResult(text=text, model=self.model, cost_usd=round(cost, 6))
