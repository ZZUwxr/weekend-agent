"""AgentEventEmitter — bridges ReAct runtime actions/observations to SSE events."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from local_explorer_agent.app.agent.react.actions import AgentAction
from local_explorer_agent.app.agent.react.state import AgentObservation
from local_explorer_agent.app.domain.models import PlanOutput
from local_explorer_agent.app.domain.schemas import PlanPreviewStreamEvent

logger = logging.getLogger(__name__)

# Maps action_type to a human-readable label for legacy compat
_ACTION_LABELS: dict[str, str] = {
    "call_tool": "调用工具",
    "validate_plan": "校验约束",
    "repair_plan": "修复方案",
    "score_plan": "评分推荐",
    "update_state": "更新状态",
    "ask_clarification": "请求澄清",
    "final_answer": "输出方案",
    "fail": "标记失败",
}


class AgentEventEmitter:
    """Converts runtime events into SSE-compatible PlanPreviewStreamEvent objects.

    When callback is None, all methods are no-ops (non-streaming mode).
    Emits both new agent events and legacy compat events.
    """

    def __init__(
        self,
        callback: Callable[[PlanPreviewStreamEvent], None] | None,
    ) -> None:
        self._callback = callback

    def _emit(self, event: PlanPreviewStreamEvent) -> None:
        if self._callback is not None:
            try:
                self._callback(event)
            except Exception:
                logger.warning("Failed to emit SSE event", exc_info=True)

    async def emit_action(self, step_index: int, action: AgentAction) -> None:
        action_type = action.action_type
        tool_name = action.tool_name

        # New agent_action event
        self._emit(PlanPreviewStreamEvent(
            event="agent_action",
            data={
                "step_index": step_index,
                "action_type": action_type,
                "tool_name": tool_name,
                "decision_summary": action.decision_summary,
            },
        ))

        if action.tool_name:
            self._emit(PlanPreviewStreamEvent(
                event="tool_call",
                data={
                    "step": step_index,
                    "tool": tool_name,
                    "action": action_type,
                    "params": _compact_mapping(action.tool_args),
                    "result": {"success": None, "latency_ms": 0},
                },
            ))

        if str(action.action_type) == "ask_clarification":
            self._emit(PlanPreviewStreamEvent(
                event="clarification_required",
                data={
                    "step_index": step_index,
                    "message": action.message,
                    "decision_summary": action.decision_summary,
                },
            ))

        # Legacy step_start compat
        label = _ACTION_LABELS.get(action_type, action_type)
        self._emit(PlanPreviewStreamEvent(
            event="step_start",
            data={
                "step": step_index,
                "name": tool_name or action_type,
                "label": label,
            },
        ))

    async def emit_observation(
        self, step_index: int, observation: AgentObservation
    ) -> None:
        tool_name = observation.tool_name
        data_summary = _summarize_observation_data(observation.data)

        # New tool_observation event
        self._emit(PlanPreviewStreamEvent(
            event="tool_observation",
            data={
                "step_index": step_index,
                "tool_name": tool_name,
                "success": observation.success,
                "summary": data_summary,
                "error": observation.error,
            },
        ))

        # Legacy step_complete compat
        self._emit(PlanPreviewStreamEvent(
            event="step_complete",
            data={
                "step": step_index,
                "name": tool_name or observation.action_type,
                "label": tool_name or observation.action_type,
                "result": {"success": observation.success, "summary": data_summary},
            },
        ))

        # Emit specialized events based on observation content
        if observation.tool_name == "validate_plan_constraints" and observation.success:
            vr = observation.data
            self._emit(PlanPreviewStreamEvent(
                event="plan_revalidated",
                data={
                    "passed": vr.get("passed", False),
                    "blocking_count": len(vr.get("blocking_violations", [])),
                    "warning_count": len(vr.get("warnings", [])),
                },
            ))
            if vr and not vr.get("passed", True):
                self._emit(PlanPreviewStreamEvent(
                    event="constraint_violation_found",
                    data={
                        "blocking_count": len(vr.get("blocking_violations", [])),
                        "warning_count": len(vr.get("warnings", [])),
                    },
                ))

        if observation.tool_name == "repair_plan" and observation.success:
            actions = observation.data.get("repair_actions_taken", [])
            self._emit(PlanPreviewStreamEvent(
                event="plan_repaired",
                data={"actions_taken": actions},
            ))

        if observation.tool_name == "score_candidates" and observation.success:
            self._emit(PlanPreviewStreamEvent(
                event="plan_rescored",
                data={
                    "recommended_plan_id": observation.data.get("recommended_plan_id"),
                },
            ))
            self._emit(PlanPreviewStreamEvent(
                event="score_updated",
                data={
                    "recommended_plan_id": observation.data.get("recommended_plan_id"),
                    "scoring_summary": observation.data.get("scoring_summary", {}),
                },
            ))

        if observation.tool_name == "interpret_revision_request" and observation.success:
            self._emit(PlanPreviewStreamEvent(
                event="revision_intent_detected",
                data={
                    "intents": observation.data.get("intents", []),
                    "target_plan_id": observation.data.get("target_plan_id"),
                },
            ))

        if (
            observation.tool_name in {
                "replace_poi",
                "apply_plan_patch",
                "revise_dining_stage",
                "add_followup_stage",
                "remove_followup_stage",
            }
            and observation.success
        ):
            patches = observation.data.get("patches", [])
            if patches:
                self._emit(PlanPreviewStreamEvent(
                    event="plan_patch_proposed",
                    data={"patches": [_compact_mapping(patch) for patch in patches]},
                ))
                self._emit(PlanPreviewStreamEvent(
                    event="plan_patch_applied",
                    data={"patch_count": len(patches)},
                ))

    async def emit_state_updated(self, step_index: int, state: Any) -> None:
        self._emit(PlanPreviewStreamEvent(
            event="state_updated",
            data={
                "step_index": step_index,
                "status": state.status,
                "step_count": state.step_count,
                "tool_call_count": state.tool_call_count,
            },
        ))

    async def emit_plan_complete(self, plan: PlanOutput) -> None:
        self._emit(PlanPreviewStreamEvent(
            event="plan_complete",
            data={
                "session_id": plan.session_id,
                "recommended_plan_id": plan.recommended_plan_id,
                "candidates_count": len(plan.plan_candidates),
            },
        ))

    async def emit_revision_started(self, step_index: int, session_id: str) -> None:
        self._emit(PlanPreviewStreamEvent(
            event="revision_started",
            data={"step_index": step_index, "session_id": session_id},
        ))

    async def emit_revision_complete(self, plan: PlanOutput) -> None:
        self._emit(PlanPreviewStreamEvent(
            event="revision_complete",
            data={
                "session_id": plan.session_id,
                "plan_version": plan.plan_version,
                "summary": (
                    plan.revision_summary.summary
                    if plan.revision_summary is not None
                    else ""
                ),
            },
        ))

    async def emit_error(
        self, error: str, step_index: int | None = None
    ) -> None:
        self._emit(PlanPreviewStreamEvent(
            event="error",
            data={"step": step_index, "error": error, "message": error},
        ))


def _summarize_observation_data(data: dict[str, Any]) -> str:
    if not data:
        return ""

    if "candidates" in data:
        n = len(data["candidates"])
        return f"生成 {n} 个候选方案"

    if "conflicts" in data:
        n = len(data["conflicts"])
        return f"检测到 {n} 个冲突"

    if "strategies" in data:
        n = len(data["strategies"])
        return f"生成 {n} 个协商策略"

    if "passed" in data:
        status = "通过" if data["passed"] else "未通过"
        blocking = len(data.get("blocking_violations", []))
        warns = len(data.get("warnings", []))
        return f"校验{status}，{blocking} 个阻塞，{warns} 个警告"

    if "repair_actions_taken" in data:
        n = len(data["repair_actions_taken"])
        return f"执行 {n} 个修复操作"

    if "recommended_plan_id" in data:
        return f"推荐方案: {data['recommended_plan_id']}"

    keys = list(data.keys())[:3]
    return f"数据字段: {', '.join(keys)}"


def _compact_mapping(data: dict[str, Any], max_items: int = 8) -> dict[str, Any]:
    compact: dict[str, Any] = {}
    for key, value in list(data.items())[:max_items]:
        if isinstance(value, str):
            compact[key] = value[:160]
        elif isinstance(value, int | float | bool) or value is None:
            compact[key] = value
        elif isinstance(value, list):
            compact[key] = value[:5]
        elif isinstance(value, dict):
            compact[key] = {k: value[k] for k in list(value.keys())[:5]}
        else:
            compact[key] = str(value)[:160]
    return compact
