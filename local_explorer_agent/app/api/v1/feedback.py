from typing import Annotated

from fastapi import APIRouter, Depends

from local_explorer_agent.app.api.deps import get_feedback_service
from local_explorer_agent.app.domain.schemas import FeedbackRequest, FeedbackResponse
from local_explorer_agent.app.services.feedback_service import FeedbackService

router = APIRouter(prefix="/plans", tags=["feedback"])


@router.post("/{session_id}/feedback", response_model=FeedbackResponse)
def submit_feedback(
    session_id: str,
    request: FeedbackRequest,
    service: Annotated[FeedbackService, Depends(get_feedback_service)],
) -> FeedbackResponse:
    return service.submit_feedback(session_id, request)
