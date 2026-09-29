"""
POST /feedback — records human feedback on a past answer, keyed by
trace_id, so you can build a dataset for evaluation/fine-tuning later.
"""
from fastapi import APIRouter

from ragagent.api.schemas import FeedbackRequest
from ragagent.observability.logger import logger

router = APIRouter()


@router.post("/feedback")
def feedback(request: FeedbackRequest) -> dict:
    # TODO: persist feedback (DB table keyed by trace_id) rather than just logging
    logger.info("Feedback received", extra={
        "trace_id": request.trace_id,
        "rating": request.rating,
        "comment": request.comment,
    })
    return {"status": "recorded", "trace_id": request.trace_id}
