"""Background worker: poll the queue, run the pipeline, record the outcome.

The worker is the same Docker image as the api, started with a different command
(``python -m app.worker``). It owns no HTTP surface — it just claims one job at a
time and runs the six pipeline steps. Heartbeats and per-step progress are handled
inside ``run_pipeline``; here we only claim, run, and mark done/failed.

The pipeline package is built by a separate agent, so its import is deferred into
``run_once`` — the rest of this module (and the queue tests) import cleanly even
before the pipeline exists.
"""

from __future__ import annotations

import logging
import time
import uuid

from app.config import Settings, get_settings
from app.db.models import Analysis
from app.db.session import SessionLocal
from app.jobs.queue import claim_next

logger = logging.getLogger("yanki.worker")


def run_once(settings: Settings) -> bool:
    """Claim and run at most one job. Returns True if a job was processed."""
    session = SessionLocal()
    try:
        analysis = claim_next(session, settings)
        if analysis is None:
            return False

        analysis_id: uuid.UUID = analysis.id
        try:
            from app.pipeline.runner import run_pipeline

            run_pipeline(session, analysis_id, settings)
        except Exception as exc:
            # Keep whatever partial rows earlier steps committed (FR-7); only the
            # in-flight step's uncommitted work is rolled back.
            session.rollback()
            failed = session.get(Analysis, analysis_id)
            if failed is not None:
                failed.status = "failed"
                failed.error = str(exc)[:500]
                session.commit()
            logger.exception("analysis %s failed", analysis_id)
            return True

        done = session.get(Analysis, analysis_id)
        if done is not None:
            done.status = "done"
            done.progress = 100
            done.current_step = None
            session.commit()
        return True
    finally:
        session.close()


def main() -> None:
    settings = get_settings()
    logger.info("worker starting (dry_run=%s)", settings.dry_run)
    while True:
        try:
            run_once(settings)
        except Exception:
            logger.exception("worker loop error")
        time.sleep(settings.worker_poll_seconds)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
