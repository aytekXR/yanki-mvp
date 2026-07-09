"""Real OpenAI provider (gpt-4o-mini) via the official SDK.

Cost is estimated from the token usage the API reports, using a simple price
table constant. Only ever called when ``DRY_RUN`` is off.
"""

from __future__ import annotations

from app.providers.base import ProviderResult

MODEL = "gpt-4o-mini"
MAX_TOKENS = 1024

# gpt-4o-mini list price: $0.15 / 1M input tokens, $0.60 / 1M output tokens.
INPUT_PRICE_PER_TOKEN = 0.15 / 1_000_000
OUTPUT_PRICE_PER_TOKEN = 0.60 / 1_000_000


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
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        text = completion.choices[0].message.content or ""
        usage = completion.usage
        cost = (
            usage.prompt_tokens * INPUT_PRICE_PER_TOKEN
            + usage.completion_tokens * OUTPUT_PRICE_PER_TOKEN
        )
        return ProviderResult(text=text, model=self.model, cost_usd=round(cost, 6))
