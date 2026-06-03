from typing import Annotated

from fastapi import APIRouter, Depends, Query

from local_explorer_agent.app.api.deps import get_feedback_followup_service
from local_explorer_agent.app.domain.followup import FeedbackFollowupTask
from local_explorer_agent.app.domain.schemas import (
    FeedbackFollowupResponse,
    FeedbackFollowupSubmitRequest,
    FeedbackFollowupSubmitResponse,
)
from local_explorer_agent.app.services.feedback_followup_service import (
    FeedbackFollowupService,
)

router = APIRouter(prefix="/plans", tags=["feedback-followup"])


@router.get("/{session_id}/feedback-followup", response_model=FeedbackFollowupResponse)
def get_feedback_followup(
    session_id: str,
    service: Annotated[FeedbackFollowupService, Depends(get_feedback_followup_service)],
) -> FeedbackFollowupResponse:
    return FeedbackFollowupResponse(task=service.get_for_session(session_id))


@router.post(
    "/{session_id}/feedback-followup",
    response_model=FeedbackFollowupSubmitResponse,
)
def submit_feedback_followup(
    session_id: str,
    request: FeedbackFollowupSubmitRequest,
    service: Annotated[FeedbackFollowupService, Depends(get_feedback_followup_service)],
) -> FeedbackFollowupSubmitResponse:
    return service.submit_response(session_id, request)


@router.get("/feedback-followups/due", response_model=list[FeedbackFollowupTask])
def list_due_feedback_followups(
    service: Annotated[FeedbackFollowupService, Depends(get_feedback_followup_service)],
    user_id: str | None = Query(default=None),
) -> list[FeedbackFollowupTask]:
    return service.list_due(user_id=user_id)
