"""HTTP routes for analyses (POST to submit, GET to poll status/results)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import (
    AnalysisOut,
    CreateAnalysisRequest,
    CreateAnalysisResponse,
    PromptOut,
    ResponseOut,
    ResultOut,
)
from app.db.models import Analysis
from app.db.session import get_session
from app.services.analyses import create_analysis, get_analysis

router = APIRouter(prefix="/api/v1", tags=["analyses"])


def _to_out(analysis: Analysis) -> AnalysisOut:
    """Build the full GET envelope from an ORM row. ``result`` is always present."""
    result = ResultOut(
        kyc=analysis.kyc,
        prompts=[PromptOut.model_validate(p) for p in analysis.prompts],
        responses=[ResponseOut.model_validate(r) for r in analysis.responses],
        geo_score=analysis.geo_score,
        footprint_count=analysis.footprint_count,
        total_responses=analysis.total_responses,
    )
    return AnalysisOut(
        id=analysis.id,
        url=analysis.url,
        status=analysis.status,
        progress=analysis.progress,
        current_step=analysis.current_step,
        error=analysis.error,
        created_at=analysis.created_at,
        updated_at=analysis.updated_at,
        result=result,
    )


@router.post("/analyses", status_code=202, response_model=CreateAnalysisResponse)
def submit_analysis(
    payload: CreateAnalysisRequest,
    session: Session = Depends(get_session),
) -> CreateAnalysisResponse:
    analysis = create_analysis(session, str(payload.url))
    return CreateAnalysisResponse(id=analysis.id)


@router.get("/analyses/{analysis_id}", response_model=AnalysisOut)
def read_analysis(
    analysis_id: uuid.UUID,
    session: Session = Depends(get_session),
) -> AnalysisOut:
    analysis = get_analysis(session, analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="analysis not found")
    return _to_out(analysis)
