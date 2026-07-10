"""HTTP routes for analyses (POST to submit, GET to poll status/results)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.schemas import (
    AnalysisOut,
    CheckerLeadRequest,
    CheckerSubmitRequest,
    CheckerSubmitResponse,
    CreateAnalysisRequest,
    CreateAnalysisResponse,
    PromptOut,
    ResponseOut,
    ResultOut,
)
from app.config import Settings, get_settings
from app.db.models import Analysis
from app.db.session import get_session
from app.net_guard import is_public_url
from app.services.analyses import create_analysis, get_analysis
from app.services.checker import attach_lead, create_checker_analysis
from app.services.rate_limit import (
    RateLimitExceeded,
    check_rate_limit,
    client_ip,
    hash_ip,
)

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
    request: Request,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> CreateAnalysisResponse:
    # Reject SSRF targets (loopback/private/link-local/metadata) up front; the
    # worker's discovery step re-checks every redirect hop as defence in depth.
    # This runs first and returns 422 without creating a row, so SSRF-rejected
    # submits never count toward the rate limit (the limit counts rows).
    if not is_public_url(str(payload.url)):
        raise HTTPException(status_code=422, detail="URL host is not allowed")

    # Rate-limit BEFORE create_analysis so a throttled client never gets a row
    # or spends money — even for an otherwise-valid URL.
    ip_hash = hash_ip(client_ip(request) or "unknown", settings.ip_hash_salt)
    try:
        check_rate_limit(session, ip_hash, settings)
    except RateLimitExceeded as exc:
        raise HTTPException(
            status_code=429,
            detail="rate limit exceeded",
            headers={"Retry-After": str(exc.retry_after)},
        ) from exc

    analysis = create_analysis(session, str(payload.url), ip_hash=ip_hash)
    return CreateAnalysisResponse(id=analysis.id)


@router.post("/checker", status_code=202, response_model=CheckerSubmitResponse)
def submit_checker(
    payload: CheckerSubmitRequest,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> CheckerSubmitResponse:
    # Blank brand/category is rejected by the schema (422) before we get here, so
    # an invalid submit records nothing. This route does NOT rate-limit or gate
    # on a kill-switch — that is P5.6's job (which also fills ip_hash).
    analysis, submission = create_checker_analysis(
        session, payload.brand, payload.category, payload.lang, settings
    )
    return CheckerSubmitResponse(id=analysis.id, submission_id=submission.id)


@router.post("/checker/leads", status_code=202)
def submit_checker_lead(
    payload: CheckerLeadRequest,
    session: Session = Depends(get_session),
) -> dict[str, str]:
    submission = attach_lead(session, payload.submission_id, payload.email)
    if submission is None:
        raise HTTPException(status_code=404, detail="submission not found")
    return {"status": "ok"}


@router.get("/analyses/{analysis_id}", response_model=AnalysisOut)
def read_analysis(
    analysis_id: uuid.UUID,
    session: Session = Depends(get_session),
) -> AnalysisOut:
    analysis = get_analysis(session, analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="analysis not found")
    return _to_out(analysis)
