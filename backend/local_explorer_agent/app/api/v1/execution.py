from typing import Annotated

from fastapi import APIRouter, Depends

from local_explorer_agent.app.api.deps import get_execution_service
from local_explorer_agent.app.domain.schemas import ExecutionResponse
from local_explorer_agent.app.services.execution_service import ExecutionService

router = APIRouter(prefix="/plans", tags=["execution"])


@router.post("/{session_id}/execute", response_model=ExecutionResponse)
def execute_plan(
    session_id: str,
    service: Annotated[ExecutionService, Depends(get_execution_service)],
) -> ExecutionResponse:
    return service.execute(session_id)
