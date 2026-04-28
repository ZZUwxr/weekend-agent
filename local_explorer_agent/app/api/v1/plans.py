from typing import Annotated

from fastapi import APIRouter, Depends

from local_explorer_agent.app.api.deps import get_plan_service
from local_explorer_agent.app.domain.models import PlanOutput
from local_explorer_agent.app.domain.schemas import PlanPreviewRequest
from local_explorer_agent.app.services.plan_service import PlanService

router = APIRouter(prefix="/plans", tags=["plans"])


@router.post("/preview", response_model=PlanOutput)
def preview_plan(
    request: PlanPreviewRequest,
    service: Annotated[PlanService, Depends(get_plan_service)],
) -> PlanOutput:
    return service.preview_plan(request)


@router.get("/{session_id}", response_model=PlanOutput)
def get_plan(
    session_id: str,
    service: Annotated[PlanService, Depends(get_plan_service)],
) -> PlanOutput:
    return service.get_plan(session_id)


@router.post("/{session_id}/confirm", response_model=PlanOutput)
def confirm_plan(
    session_id: str,
    service: Annotated[PlanService, Depends(get_plan_service)],
) -> PlanOutput:
    return service.confirm_plan(session_id)
