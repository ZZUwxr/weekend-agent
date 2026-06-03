from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from local_explorer_agent.app.agent.react.actions import AgentAction
    from local_explorer_agent.app.agent.react.state import AgentState
    from local_explorer_agent.app.agent.react.tool_registry import ToolSpec


class AgentDecider(Protocol):
    async def decide(
        self,
        state: AgentState,
        tools: list[ToolSpec],
    ) -> AgentAction: ...
