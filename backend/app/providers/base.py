"""The provider interface every engine adapter implements.

Every adapter exposes ``name`` (the panel engine name), ``model`` (the model
string recorded on each response) and a single ``generate(prompt)`` call that
returns a :class:`ProviderResult`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class ProviderResult:
    """The output of one provider call."""

    text: str
    model: str
    cost_usd: float


@runtime_checkable
class Provider(Protocol):
    name: str
    model: str

    def generate(self, prompt: str) -> ProviderResult:
        ...
