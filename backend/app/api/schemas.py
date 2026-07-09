"""Pydantic request/response schemas — the locked API contract.

The GET response always carries a ``result`` envelope; its inner fields are
null/empty until the pipeline produces them, so the frontend can render partial
state (and failures keep their partial results queryable — FR-7).
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import AnyHttpUrl, BaseModel, ConfigDict


class CreateAnalysisRequest(BaseModel):
    # AnyHttpUrl accepts http/https URLs only; anything else is a 422.
    url: AnyHttpUrl


class CreateAnalysisResponse(BaseModel):
    id: uuid.UUID


class PromptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    text: str
    category: str


class ResponseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    prompt_id: uuid.UUID
    engine: str
    model: str
    raw_text: str
    footprint: bool | None
    matched_snippet: str | None
    cost_usd: float


class ResultOut(BaseModel):
    kyc: dict[str, Any] | None
    prompts: list[PromptOut]
    responses: list[ResponseOut]
    geo_score: float | None
    footprint_count: int | None
    total_responses: int | None


class AnalysisOut(BaseModel):
    id: uuid.UUID
    url: str
    status: str
    progress: int
    current_step: str | None
    error: str | None
    created_at: datetime
    updated_at: datetime
    result: ResultOut
