from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from local_explorer_agent.app.agent.react.actions import AgentAction, AgentActionType
from local_explorer_agent.app.agent.react.exceptions import ReActError
from local_explorer_agent.app.agent.react.state import AgentObservation

if TYPE_CHECKING:
    from local_explorer_agent.app.agent.react.state import AgentState
    from local_explorer_agent.app.agent.react.tool_registry import ToolRegistry


class ActionExecutor:
    def __init__(self, tool_registry: ToolRegistry) -> None:
        self.tool_registry = tool_registry

    async def execute(self, action: AgentAction, state: AgentState) -> AgentObservation:
        handler = self._get_handler(action.action_type)
        return await handler(action, state)

    _TOOL_ACTION_MAP: dict[str, str] = {
        "validate_plan": "validate_plan_constraints",
        "repair_plan": "repair_plan",
        "score_plan": "score_candidates",
    }

    def _get_handler(self, action_type: AgentActionType):  # type: ignore[no-untyped-def]
        handlers = {
            AgentActionType.CALL_TOOL: self._execute_call_tool,
            AgentActionType.UPDATE_STATE: self._execute_update_state,
            AgentActionType.ASK_CLARIFICATION: self._execute_passthrough,
            AgentActionType.FINAL_ANSWER: self._execute_passthrough,
            AgentActionType.FAIL: self._execute_passthrough,
            AgentActionType.VALIDATE_PLAN: self._execute_tool_action,
            AgentActionType.REPAIR_PLAN: self._execute_tool_action,
            AgentActionType.SCORE_PLAN: self._execute_tool_action,
        }
        handler = handlers.get(action_type)
        if handler is None:
            raise ReActError(
                f"Action type '{action_type}' is not implemented in this phase"
            )
        return handler

    async def _execute_call_tool(
        self, action: AgentAction, state: AgentState
    ) -> AgentObservation:
        tool = self.tool_registry.get(action.tool_name)  # type: ignore[arg-type]

        try:
            args_model = tool.args_schema.model_validate(action.tool_args)
        except Exception as exc:
            return AgentObservation(
                action_type=AgentActionType.CALL_TOOL,
                tool_name=action.tool_name,
                success=False,
                error=f"Argument validation failed: {exc}",
                created_at=datetime.now(UTC),
            )

        try:
            result = await tool.run(args_model, state)
            return AgentObservation(
                action_type=AgentActionType.CALL_TOOL,
                tool_name=action.tool_name,
                success=result.success,
                data=result.data if isinstance(result.data, dict) else {"result": result.data},
                error=result.error_message,
                created_at=datetime.now(UTC),
            )
        except Exception as exc:
            return AgentObservation(
                action_type=AgentActionType.CALL_TOOL,
                tool_name=action.tool_name,
                success=False,
                error=str(exc),
                created_at=datetime.now(UTC),
            )

    async def _execute_update_state(
        self, action: AgentAction, state: AgentState
    ) -> AgentObservation:
        return AgentObservation(
            action_type=AgentActionType.UPDATE_STATE,
            success=True,
            data=action.state_patch,
            created_at=datetime.now(UTC),
        )

    async def _execute_passthrough(
        self, action: AgentAction, state: AgentState
    ) -> AgentObservation:
        return AgentObservation(
            action_type=action.action_type,
            success=True,
            data={"message": action.message} if action.message else {},
            created_at=datetime.now(UTC),
        )

    async def _execute_tool_action(
        self, action: AgentAction, state: AgentState
    ) -> AgentObservation:
        tool_name = self._TOOL_ACTION_MAP[action.action_type]
        tool = self.tool_registry.get(tool_name)

        try:
            args_model = tool.args_schema.model_validate(action.tool_args)
        except Exception as exc:
            return AgentObservation(
                action_type=action.action_type,
                tool_name=tool_name,
                success=False,
                error=f"Argument validation failed: {exc}",
                created_at=datetime.now(UTC),
            )

        try:
            result = await tool.run(args_model, state)
            return AgentObservation(
                action_type=action.action_type,
                tool_name=tool_name,
                success=result.success,
                data=result.data if isinstance(result.data, dict) else {"result": result.data},
                error=result.error_message,
                created_at=datetime.now(UTC),
            )
        except Exception as exc:
            return AgentObservation(
                action_type=action.action_type,
                tool_name=tool_name,
                success=False,
                error=str(exc),
                created_at=datetime.now(UTC),
            )
