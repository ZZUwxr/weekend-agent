from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from local_explorer_agent.app.agent.react.exceptions import DuplicateToolError, ToolNotFoundError
from local_explorer_agent.app.tools.base import ToolResult

if TYPE_CHECKING:
    from local_explorer_agent.app.agent.react.state import AgentState


class ToolSpec(BaseModel):
    name: str
    description: str
    args_schema: dict[str, Any] = Field(default_factory=dict)
    is_execution_tool: bool = False
    requires_confirmation: bool = False
    prepare_tool: bool = False


@runtime_checkable
class AgentTool(Protocol):
    name: str
    description: str
    args_schema: type[BaseModel]
    is_execution_tool: bool
    requires_confirmation: bool

    async def run(self, args: BaseModel, state: AgentState) -> ToolResult: ...


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, AgentTool] = {}

    def register(self, tool: AgentTool) -> None:
        if tool.name in self._tools:
            raise DuplicateToolError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool

    def get(self, name: str) -> AgentTool:
        tool = self._tools.get(name)
        if tool is None:
            raise ToolNotFoundError(f"Tool '{name}' is not registered")
        return tool

    def list_specs(self) -> list[ToolSpec]:
        specs: list[ToolSpec] = []
        for tool in self._tools.values():
            schema = (
                tool.args_schema.model_json_schema()
                if hasattr(tool.args_schema, "model_json_schema")
                else {}
            )
            specs.append(
                ToolSpec(
                    name=tool.name,
                    description=tool.description,
                    args_schema=schema,
                    is_execution_tool=tool.is_execution_tool,
                    requires_confirmation=tool.requires_confirmation,
                    prepare_tool=bool(getattr(tool, "prepare_tool", False)),
                )
            )
        return specs
