from __future__ import annotations

from typing import TYPE_CHECKING

from local_explorer_agent.app.agent.react.actions import AgentAction, AgentActionType
from local_explorer_agent.app.agent.react.exceptions import PolicyViolationError
from local_explorer_agent.app.domain.validation import PlanValidationResult

if TYPE_CHECKING:
    from local_explorer_agent.app.agent.react.state import AgentState
    from local_explorer_agent.app.agent.react.tool_registry import ToolRegistry

_PREVIEW_BLOCKED_EXECUTION_TOOLS = {
    "booking_tool",
    "taxi_tool",
    "share_tool",
    "booking_execute",
    "taxi_execute",
    "share_execute",
}
_SPECIAL_ACTION_TOOLS = {
    AgentActionType.VALIDATE_PLAN: "validate_plan_constraints",
    AgentActionType.REPAIR_PLAN: "repair_plan",
    AgentActionType.SCORE_PLAN: "score_candidates",
}
_CORE_PLANNING_TOOLS = {
    "understand_user",
    "detect_conflicts",
    "generate_negotiation_strategy",
    "draft_experience_plan",
    "select_places",
    "calculate_routes",
    "build_timeline",
}
_POST_CONFLICT_TOOLS = {
    "draft_experience_plan",
    "select_places",
    "calculate_routes",
    "build_timeline",
}


class AgentPolicy:
    def __init__(
        self,
        max_steps: int = 20,
        max_tool_calls: int = 30,
        max_repair_attempts: int = 2,
        max_revision_attempts: int = 5,
    ) -> None:
        self.max_steps = max_steps
        self.max_tool_calls = max_tool_calls
        self.max_repair_attempts = max_repair_attempts
        self.max_revision_attempts = max_revision_attempts

    def validate_action(
        self,
        action: AgentAction,
        state: AgentState,
        tool_registry: ToolRegistry,
    ) -> None:
        if state.step_count >= self.max_steps:
            raise PolicyViolationError(
                f"Max steps ({self.max_steps}) exceeded at step {state.step_count}"
            )

        if state.tool_call_count >= self.max_tool_calls:
            raise PolicyViolationError(
                f"Max tool calls ({self.max_tool_calls}) exceeded at {state.tool_call_count}"
            )

        self._validate_action_tool_shape(action)

        if action.action_type == AgentActionType.CALL_TOOL:
            self._validate_tool_call(action, tool_registry)

        if (
            action.action_type != AgentActionType.FINAL_ANSWER
            and not state.is_revision
            and not state.is_replan
        ):
            self._validate_intake_gate(action, state)
            self._validate_conflict_gate(action, state)

        if state.is_revision and state.revision_count >= self.max_revision_attempts:
            raise PolicyViolationError(
                f"Cannot revise after {self.max_revision_attempts} revision attempts"
            )

        if action.action_type in (
            AgentActionType.VALIDATE_PLAN,
            AgentActionType.REPAIR_PLAN,
            AgentActionType.SCORE_PLAN,
        ):
            if not state.candidate_plans:
                raise PolicyViolationError(
                    f"Cannot {action.action_type} without candidate_plans"
                )

        if action.action_type == AgentActionType.ASK_CLARIFICATION:
            clarification = state.clarification_response
            if (
                clarification is None
                or not clarification.needs_clarification
                or clarification.can_continue_with_assumptions
                or not any(question.required for question in clarification.questions)
                or state.clarification_answers
            ):
                raise PolicyViolationError(
                    "Cannot ask optional clarification when safe assumptions allow continuing"
                )

        if _is_repair_action(action):
            self._validate_repair_action(state)
            if state.validation_result is None:
                raise PolicyViolationError(
                    "Cannot repair_plan without validation_result"
                )

        if action.action_type == AgentActionType.FINAL_ANSWER:
            self._validate_final_answer(state)

    def _validate_action_tool_shape(self, action: AgentAction) -> None:
        if action.action_type == AgentActionType.CALL_TOOL:
            if not action.tool_name:
                raise PolicyViolationError("call_tool action requires tool_name")
            return

        expected_tool = _SPECIAL_ACTION_TOOLS.get(action.action_type)
        if expected_tool and action.tool_name and action.tool_name != expected_tool:
            raise PolicyViolationError(
                f"{action.action_type} action cannot use tool_name '{action.tool_name}'"
            )

        if expected_tool is None and action.tool_name:
            raise PolicyViolationError(
                f"{action.action_type} action must not include tool_name"
            )

    def _validate_tool_call(self, action: AgentAction, tool_registry: ToolRegistry) -> None:
        if not action.tool_name:
            raise PolicyViolationError("call_tool action requires tool_name")

        tool = tool_registry.get(action.tool_name)

        if action.tool_name in _PREVIEW_BLOCKED_EXECUTION_TOOLS or tool.is_execution_tool:
            raise PolicyViolationError(
                f"Execution tool '{action.tool_name}' is not allowed during preview phase"
            )

    def _validate_intake_gate(self, action: AgentAction, state: AgentState) -> None:
        if (
            action.action_type != AgentActionType.CALL_TOOL
            or action.tool_name not in _CORE_PLANNING_TOOLS
        ):
            return

        if state.user_memory is None:
            raise PolicyViolationError(
                "Must read_user_memory before requirement intake and planning"
            )
            return

        if state.requirement_intake is None:
            raise PolicyViolationError(
                "Must call intake_user_requirements before planning"
            )
            return

        if _required_clarification_pending(state):
            if action.action_type != AgentActionType.ASK_CLARIFICATION:
                raise PolicyViolationError(
                    "Must ask_clarification before planning with missing required slots"
                )

    def _validate_conflict_gate(self, action: AgentAction, state: AgentState) -> None:
        if state.inferred_context is None:
            return

        if (
            action.action_type == AgentActionType.CALL_TOOL
            and action.tool_name == "generate_negotiation_strategy"
        ):
            if not _conflict_detection_done(state):
                raise PolicyViolationError(
                    "Must call detect_conflicts before generate_negotiation_strategy"
                )
            if not state.conflicts:
                raise PolicyViolationError(
                    "Cannot call generate_negotiation_strategy without conflicts"
                )
            return

        is_post_conflict_tool = (
            action.action_type == AgentActionType.CALL_TOOL
            and action.tool_name in _POST_CONFLICT_TOOLS
        )
        is_post_conflict_action = action.action_type in (
            AgentActionType.VALIDATE_PLAN,
            AgentActionType.SCORE_PLAN,
        )
        if not is_post_conflict_tool and not is_post_conflict_action:
            return

        if not _conflict_detection_done(state):
            raise PolicyViolationError(
                "Must call detect_conflicts before drafting or later planning"
            )

        if state.conflicts and not _negotiation_done(state):
            raise PolicyViolationError(
                "Must call generate_negotiation_strategy before planning with conflicts"
            )

    def _validate_repair_action(self, state: AgentState) -> None:
        if state.repair_count >= self.max_repair_attempts:
            raise PolicyViolationError(
                f"Cannot repair_plan after {self.max_repair_attempts} repair attempts"
            )

    def _validate_final_answer(self, state: AgentState) -> None:
        if state.status == "needs_user_input":
            raise PolicyViolationError(
                "Cannot final_answer while waiting for user clarification"
            )

        clarification = state.clarification_response
        if (
            clarification is not None
            and clarification.needs_clarification
            and not clarification.can_continue_with_assumptions
            and not state.clarification_answers
        ):
            raise PolicyViolationError(
                "Cannot final_answer before required clarification is answered"
            )

        if not state.candidate_plans:
            raise PolicyViolationError(
                "Cannot final_answer without candidate_plans"
            )

        if state.inferred_context is not None:
            if not _conflict_detection_done(state):
                raise PolicyViolationError(
                    "Cannot final_answer before detect_conflicts"
                )
            if state.conflicts and not _negotiation_done(state):
                raise PolicyViolationError(
                    "Cannot final_answer before generate_negotiation_strategy"
                )

        if state.validation_result is None:
            raise PolicyViolationError(
                "Cannot final_answer without validation_result"
            )

        vr = state.validation_result
        if isinstance(vr, PlanValidationResult) and not vr.passed:
            raise PolicyViolationError(
                "Cannot final_answer with failed validation"
            )

        if isinstance(vr, PlanValidationResult) and vr.blocking_violations:
            raise PolicyViolationError(
                "Cannot final_answer with blocking violations"
            )

        if not state.scoring_completed:
            raise PolicyViolationError(
                "Cannot final_answer without scoring_completed"
            )

        if _has_unselected_stage(state):
            raise PolicyViolationError(
                "Cannot final_answer before select_places completes"
            )

        if any(_candidate_needs_route(candidate) for candidate in state.candidate_plans):
            raise PolicyViolationError(
                "Cannot final_answer before calculate_routes completes"
            )

        if any(not candidate.timeline for candidate in state.candidate_plans):
            raise PolicyViolationError(
                "Cannot final_answer without timeline"
            )

        candidate_ids = {candidate.plan_id for candidate in state.candidate_plans}
        if not state.recommended_plan_id:
            raise PolicyViolationError(
                "Cannot final_answer without recommended_plan_id"
            )
        if state.recommended_plan_id not in candidate_ids:
            raise PolicyViolationError(
                "Cannot final_answer with recommended_plan_id outside candidate_plans"
            )

        if state.is_revision and state.revision_summary is None:
            raise PolicyViolationError(
                "Cannot final_answer for revision without revision_summary"
            )


def _is_repair_action(action: AgentAction) -> bool:
    return action.action_type == AgentActionType.REPAIR_PLAN or (
        action.action_type == AgentActionType.CALL_TOOL
        and action.tool_name == "repair_plan"
    )


def _required_clarification_pending(state: AgentState) -> bool:
    clarification = state.clarification_response
    return (
        clarification is not None
        and clarification.needs_clarification
        and not clarification.can_continue_with_assumptions
        and not state.clarification_answers
    )


def _tool_succeeded(state: AgentState, tool_name: str) -> bool:
    return any(
        observation.tool_name == tool_name and observation.success
        for observation in state.observations
    )


def _conflict_detection_done(state: AgentState) -> bool:
    return bool(state.conflicts) or _tool_succeeded(state, "detect_conflicts")


def _negotiation_done(state: AgentState) -> bool:
    return bool(state.negotiation_strategies) or _tool_succeeded(
        state,
        "generate_negotiation_strategy",
    )


def _has_unselected_stage(state: AgentState) -> bool:
    return any(
        stage.selected_poi is None
        for candidate in state.candidate_plans
        for stage in candidate.stages
    )


def _candidate_needs_route(candidate) -> bool:
    selected_poi_count = sum(
        1 for stage in candidate.stages if stage.selected_poi is not None
    )
    return selected_poi_count >= 2 and not candidate.route_segments
