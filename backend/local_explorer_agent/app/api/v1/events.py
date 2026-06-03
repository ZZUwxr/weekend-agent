from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from local_explorer_agent.app.api.deps import get_plan_service
from local_explorer_agent.app.domain.models import PlanEvent, PlanOutput
from local_explorer_agent.app.services.plan_service import PlanService

router = APIRouter(prefix="/plans", tags=["events"])


@router.post("/{session_id}/events", response_model=PlanOutput)
def handle_plan_event(
    session_id: str,
    event: PlanEvent,
    service: Annotated[PlanService, Depends(get_plan_service)],
) -> PlanOutput:
    if event.session_id != session_id:
        raise HTTPException(status_code=400, detail="Path session_id must match event.session_id")
    return service.handle_event(session_id, event)
