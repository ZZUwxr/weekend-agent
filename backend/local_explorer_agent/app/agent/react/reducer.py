from __future__ import annotations

import logging
from typing import Any

from local_explorer_agent.app.agent.react.actions import AgentAction, AgentActionType
from local_explorer_agent.app.agent.react.state import (
    AgentObservation,
    AgentState,
    AgentTraceStep,
)
from local_explorer_agent.app.agent.react.trace import summarize_state
from local_explorer_agent.app.domain.memory import UserMemoryContext
from local_explorer_agent.app.domain.models import (
    ClarificationResponse,
    Conflict,
    ExecutionTask,
    GroupContext,
    NegotiationStrategy,
    PlanCandidate,
    PlanPatch,
    PlanRevisionSummary,
    RequirementIntake,
)
from local_explorer_agent.app.domain.validation import PlanValidationResult

logger = logging.getLogger(__name__)


class StateReducer:
    def reduce(
        self,
        state: AgentState,
        action: AgentAction,
        observation: AgentObservation,
    ) -> AgentState:
        trace_step = AgentTraceStep(
            step_index=state.step_count,
            action=action,
            observation=observation,
            state_summary=summarize_state(state),
        )

        updates: dict[str, Any] = {
            "trace": [*state.trace, trace_step],
            "observations": [*state.observations, observation],
            "step_count": state.step_count + 1,
        }

        if action.action_type in (
            AgentActionType.CALL_TOOL,
            AgentActionType.VALIDATE_PLAN,
            AgentActionType.REPAIR_PLAN,
            AgentActionType.SCORE_PLAN,
        ):
            updates["tool_call_count"] = state.tool_call_count + 1

        if action.action_type == AgentActionType.REPAIR_PLAN or (
            action.action_type == AgentActionType.CALL_TOOL and action.tool_name == "repair_plan"
        ):
            updates["repair_count"] = state.repair_count + 1

        if action.action_type == AgentActionType.ASK_CLARIFICATION:
            updates["status"] = "needs_user_input"
            if state.clarification_response is not None:
                updates["clarification_response"] = state.clarification_response

        if action.action_type == AgentActionType.FINAL_ANSWER:
            updates["status"] = "completed"

        if action.action_type == AgentActionType.FAIL:
            updates["status"] = "failed"

        if action.action_type == AgentActionType.UPDATE_STATE and action.state_patch:
            merged = _merge_state_patch(state, action.state_patch)
            updates.update(merged)

        if (
            action.action_type
            in (
                AgentActionType.CALL_TOOL,
                AgentActionType.VALIDATE_PLAN,
                AgentActionType.REPAIR_PLAN,
                AgentActionType.SCORE_PLAN,
            )
            and observation.success
            and observation.tool_name
        ):
            tool_updates = _apply_tool_result(state, observation.tool_name, observation.data)
            updates.update(tool_updates)

        return state.model_copy(update=updates)


def _merge_state_patch(state: AgentState, patch: dict[str, Any]) -> dict[str, Any]:
    """Extract valid top-level fields from state_patch and return update dict."""
    valid_fields = set(type(state).model_fields.keys())
    merged: dict[str, Any] = {}
    for key, value in patch.items():
        if key in valid_fields:
            merged[key] = value
    return merged


def _apply_tool_result(
    state: AgentState,
    tool_name: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    """Map tool observation data to AgentState field updates."""
    base_updates = _warnings_update(state, data)
    try:
        if tool_name == "read_user_memory":
            return {**base_updates, "user_memory": UserMemoryContext.model_validate(data)}

        if tool_name == "intake_user_requirements":
            intake = RequirementIntake.model_validate(data)
            assumptions = [
                *state.assumptions,
                *[
                    item
                    for item in intake.clarification.safe_assumptions
                    if item not in state.assumptions
                ],
            ]
            return {
                **base_updates,
                "requirement_intake": intake,
                "clarification_response": intake.clarification,
                "known_constraints": [
                    *state.known_constraints,
                    *[
                        item
                        for item in intake.known_constraints
                        if item not in state.known_constraints
                    ],
                ],
                "missing_slots": intake.missing_slots,
                "assumptions": assumptions,
            }

        if tool_name == "understand_user":
            context = GroupContext.model_validate(data)
            return {
                **base_updates,
                "inferred_context": _merge_requirement_intake_into_context(
                    context,
                    state.requirement_intake,
                )
            }

        if tool_name == "detect_conflicts":
            raw = data.get("conflicts", [])
            return {**base_updates, "conflicts": [Conflict.model_validate(c) for c in raw]}

        if tool_name == "generate_negotiation_strategy":
            raw = data.get("strategies", [])
            return {
                **base_updates,
                "negotiation_strategies": [NegotiationStrategy.model_validate(s) for s in raw],
            }

        if tool_name in (
            "draft_experience_plan",
            "select_places",
            "calculate_routes",
            "build_timeline",
        ):
            raw = data.get("candidates", [])
            return {
                **base_updates,
                "candidate_plans": [PlanCandidate.model_validate(c) for c in raw],
            }

        if tool_name == "score_candidates":
            raw = data.get("candidates", [])
            updates: dict[str, Any] = {
                **base_updates,
                "candidate_plans": [PlanCandidate.model_validate(c) for c in raw],
                "scoring_completed": True,
            }
            rec_id = data.get("recommended_plan_id")
            if rec_id:
                updates["recommended_plan_id"] = rec_id
            return updates

        if tool_name == "clarify_requirements":
            clarification = ClarificationResponse.model_validate(data)
            assumptions = [
                *state.assumptions,
                *[item for item in clarification.safe_assumptions if item not in state.assumptions],
            ]
            return {
                **base_updates,
                "clarification_response": clarification,
                "assumptions": assumptions,
            }

        if tool_name == "interpret_revision_request":
            intents = [str(intent) for intent in data.get("intents", [])]
            return {
                **base_updates,
                "revision_intents": intents,
                "known_constraints": [*state.known_constraints, *intents],
            }

        if tool_name in (
            "replace_poi",
            "apply_plan_patch",
            "revise_dining_stage",
            "add_followup_stage",
            "remove_followup_stage",
        ):
            raw = data.get("candidates", [])
            raw_patches = data.get("patches", [])
            patches = [PlanPatch.model_validate(patch) for patch in raw_patches]
            return {
                **base_updates,
                "candidate_plans": [PlanCandidate.model_validate(c) for c in raw],
                "revision_patches": [*state.revision_patches, *patches],
                "validation_result": None,
                "scoring_completed": False,
                "execution_graph": [],
                "revision_count": state.revision_count + 1 if patches else state.revision_count,
            }

        if tool_name == "rebuild_timeline":
            raw = data.get("candidates", [])
            return {
                **base_updates,
                "candidate_plans": [PlanCandidate.model_validate(c) for c in raw],
                "validation_result": None,
                "scoring_completed": False,
            }

        if tool_name == "explain_changes":
            return {**base_updates, "revision_summary": PlanRevisionSummary.model_validate(data)}

        if tool_name == "validate_plan_constraints":
            return {
                **base_updates,
                "validation_result": PlanValidationResult.model_validate(data),
            }

        if tool_name == "repair_plan":
            raw = data.get("candidates", [])
            return {
                **base_updates,
                "candidate_plans": [PlanCandidate.model_validate(c) for c in raw],
                "validation_result": None,
                "scoring_completed": False,
            }

        if tool_name in ("booking_prepare", "taxi_prepare", "share_prepare"):
            raw_tasks = []
            if "execution_task" in data:
                raw_tasks.append(data["execution_task"])
            raw_tasks.extend(data.get("execution_tasks", []))
            return {
                **base_updates,
                "execution_graph": [
                    *state.execution_graph,
                    *[ExecutionTask.model_validate(task) for task in raw_tasks],
                ]
            }

    except Exception:
        logger.warning("Failed to apply tool result for %s", tool_name, exc_info=True)

    return base_updates


def _warnings_update(state: AgentState, data: dict[str, Any]) -> dict[str, Any]:
    warnings = [str(item) for item in data.get("warnings", []) if str(item)]
    if not warnings:
        return {}
    merged = [*state.warnings]
    for warning in warnings:
        if warning not in merged:
            merged.append(warning)
    return {"warnings": merged}


def _merge_requirement_intake_into_context(
    context: GroupContext,
    intake: RequirementIntake | None,
) -> GroupContext:
    if intake is None:
        return context
    constraints = [
        *context.inferred_constraints,
        *[item for item in intake.known_constraints if item not in context.inferred_constraints],
    ]
    if intake.activity_count.max == 1:
        constraints.append("需求采集：只允许一个核心环节")
    if intake.primary_intent != "unknown":
        constraints.append(f"需求采集：核心意图为{intake.primary_intent}")
    return context.model_copy(
        update={
            "inferred_constraints": list(dict.fromkeys(constraints)),
            "clarification_questions": [
                *context.clarification_questions,
                *[
                    question.question
                    for question in intake.clarification.questions
                    if question.question not in context.clarification_questions
                ],
            ],
        }
    )
