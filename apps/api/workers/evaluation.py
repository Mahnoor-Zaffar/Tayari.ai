import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


async def generate_evaluation(interview_id: str):
    """Background task to generate interview evaluation.
    Called by APScheduler or Celery after interview completes."""
    logger.info("Generating evaluation for interview %s", interview_id)
    # TODO: Fetch interview, call AI evaluator, store result
