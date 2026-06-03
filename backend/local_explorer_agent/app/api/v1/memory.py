from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from local_explorer_agent.app.api.deps import get_user_memory_repository
from local_explorer_agent.app.domain.memory import UserMemoryContext
from local_explorer_agent.app.repositories.user_memory_repository import UserMemoryRepository

router = APIRouter(prefix="/users", tags=["memory"])


@router.get("/{user_id}/memory", response_model=UserMemoryContext)
def get_user_memory(
    user_id: str,
    repository: Annotated[UserMemoryRepository, Depends(get_user_memory_repository)],
) -> UserMemoryContext:
    try:
        return repository.get_context(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
