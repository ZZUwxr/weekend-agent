from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from local_explorer_agent.app.repositories.user_memory_repository import UserMemoryRepository
from local_explorer_agent.app.tools.base import ToolResult

if TYPE_CHECKING:
    from local_explorer_agent.app.agent.react.state import AgentState


class ReadUserMemoryArgs(BaseModel):
    user_id: str = Field(description="User ID used to load the local memory file")
    companion_ids: list[str] = Field(
        default_factory=list,
        description="Optional companion IDs selected for this planning session",
    )


class ReadUserMemoryTool:
    name = "read_user_memory"
    description = "读取用户本地记忆文件，并返回可用于规划决策的压缩偏好上下文"
    args_schema = ReadUserMemoryArgs
    is_execution_tool = False
    requires_confirmation = False

    def __init__(self, repository: UserMemoryRepository) -> None:
        self.repository = repository

    async def run(self, args: BaseModel, state: AgentState) -> ToolResult:
        assert isinstance(args, ReadUserMemoryArgs)
        try:
            context = self.repository.get_context_for_companions(
                args.user_id,
                args.companion_ids,
            )
        except ValueError as exc:
            return ToolResult(success=False, error_message=str(exc))
        return ToolResult(success=True, data=context.model_dump())
