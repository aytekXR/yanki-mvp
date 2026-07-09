"""Real Anthropic provider (Claude Haiku 4.5) via the official SDK.

Cost is estimated from the token usage the API reports, using a simple price
table constant. Only ever called when ``DRY_RUN`` is off.
"""

from __future__ import annotations

from app.providers.base import ProviderResult

MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 1024

# Claude Haiku 4.5 list price: $1.00 / 1M input tokens, $5.00 / 1M output tokens.
INPUT_PRICE_PER_TOKEN = 1.00 / 1_000_000
OUTPUT_PRICE_PER_TOKEN = 5.00 / 1_000_000


class AnthropicProvider:
    name = "anthropic"
    model = MODEL

    def __init__(self, api_key: str) -> None:
        # Imported lazily so DRY_RUN runs never need the SDK installed at import.
        import anthropic

        self._client = anthropic.Anthropic(api_key=api_key)

    def generate(self, prompt: str) -> ProviderResult:
        message = self._client.messages.create(
            model=self.model,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(
            block.text
            for block in message.content
            if getattr(block, "type", None) == "text"
        )
        usage = message.usage
        cost = (
            usage.input_tokens * INPUT_PRICE_PER_TOKEN
            + usage.output_tokens * OUTPUT_PRICE_PER_TOKEN
        )
        return ProviderResult(text=text, model=self.model, cost_usd=round(cost, 6))
