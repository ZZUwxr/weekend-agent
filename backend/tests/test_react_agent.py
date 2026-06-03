from datetime import datetime

import pytest
from pydantic import BaseModel

from local_explorer_agent.app.agent.react.actions import AgentAction, AgentActionType
from local_explorer_agent.app.agent.react.exceptions import (
    DuplicateToolError,
    PolicyViolationError,
    ToolNotFoundError,
)
from local_explorer_agent.app.agent.react.policy import AgentPolicy
from local_explorer_agent.app.agent.react.reducer import StateReducer
from local_explorer_agent.app.agent.react.state import AgentObservation, AgentState
from local_explorer_agent.app.agent.react.tool_registry import ToolRegistry
from local_explorer_agent.app.domain.schemas import PlanPreviewRequest
from local_explorer_agent.app.domain.validation import PlanValidationResult
from local_explorer_agent.app.tools.base import ToolResult

# ── helpers ──────────────────────────────────────────────────────────────────


class _DummyArgs(BaseModel):
    query: str = "test"


class _DummyTool:
    name = "dummy_tool"
    description = "A dummy tool for testing"
    args_schema = _DummyArgs
    is_execution_tool = False
    requires_confirmation = False

    async def run(self, args: BaseModel, state: AgentState) -> ToolResult:
        return ToolResult(success=True, data={"answer": 42})


def _make_request() -> PlanPreviewRequest:
    return PlanPreviewRequest(
        user_id="u_test",
        query="周末带孩子出去玩",
        city="深圳",
        start_time=datetime.fromisoformat("2026-05-10T14:00:00"),
        duration_minutes=240,
    )


def _make_state(**overrides) -> AgentState:  # type: ignore[no-untyped-def]
    base = {
        "session_id": "sess_test",
        "user_id": "u_test",
        "request": _make_request(),
    }
    base.update(overrides)
    return AgentState(**base)


# ── ToolRegistry tests ───────────────────────────────────────────────────────


def test_tool_registry_register_and_get() -> None:
    registry = ToolRegistry()
    tool = _DummyTool()
    registry.register(tool)

    got = registry.get("dummy_tool")
    assert got.name == "dummy_tool"

    specs = registry.list_specs()
    assert len(specs) == 1
    assert specs[0].name == "dummy_tool"
    assert specs[0].description == "A dummy tool for testing"


def test_tool_registry_duplicate_tool() -> None:
    registry = ToolRegistry()
    registry.register(_DummyTool())

    with pytest.raises(DuplicateToolError):
        registry.register(_DummyTool())


def test_tool_registry_unknown_tool() -> None:
    registry = ToolRegistry()

    with pytest.raises(ToolNotFoundError):
        registry.get("nonexistent_tool")


# ── Policy tests ─────────────────────────────────────────────────────────────


def test_policy_rejects_final_without_plans() -> None:
    policy = AgentPolicy(max_steps=20, max_tool_calls=30)
    registry = ToolRegistry()
    state = _make_state(
        candidate_plans=[],
        validation_result=PlanValidationResult(passed=True),
        scoring_completed=True,
    )
    action = AgentAction(
        action_type=AgentActionType.FINAL_ANSWER,
        decision_summary="done",
    )

    with pytest.raises(PolicyViolationError, match="candidate_plans"):
        policy.validate_action(action, state, registry)


def test_policy_rejects_final_without_validation() -> None:
    policy = AgentPolicy(max_steps=20, max_tool_calls=30)
    registry = ToolRegistry()
    # Use a non-empty list for candidate_plans to pass that check
    state = _make_state(
        candidate_plans=[],
        validation_result=None,
        scoring_completed=True,
    )
    action = AgentAction(
        action_type=AgentActionType.FINAL_ANSWER,
        decision_summary="done",
    )

    with pytest.raises(PolicyViolationError, match="candidate_plans"):
        policy.validate_action(action, state, registry)


def test_policy_rejects_final_without_scoring() -> None:
    policy = AgentPolicy(max_steps=20, max_tool_calls=30)
    registry = ToolRegistry()
    state = _make_state(
        candidate_plans=[],
        validation_result=PlanValidationResult(passed=True),
        scoring_completed=False,
    )
    action = AgentAction(
        action_type=AgentActionType.FINAL_ANSWER,
        decision_summary="done",
    )

    with pytest.raises(PolicyViolationError, match="candidate_plans"):
        policy.validate_action(action, state, registry)


# ── Reducer tests ────────────────────────────────────────────────────────────


def test_reducer_records_trace() -> None:
    reducer = StateReducer()
    state = _make_state()
    action = AgentAction(
        action_type=AgentActionType.UPDATE_STATE,
        state_patch={"goal": "updated"},
        decision_summary="update goal",
    )
    observation = AgentObservation(
        action_type=AgentActionType.UPDATE_STATE,
        success=True,
    )

    new_state = reducer.reduce(state, action, observation)

    assert len(new_state.trace) == 1
    assert new_state.trace[0].step_index == 0
    assert new_state.trace[0].action.decision_summary == "update goal"
    assert new_state.trace[0].observation is not None
    assert new_state.step_count == 1


def test_reducer_updates_status_on_final_answer() -> None:
    reducer = StateReducer()
    state = _make_state()
    action = AgentAction(
        action_type=AgentActionType.FINAL_ANSWER,
        decision_summary="all done",
    )
    observation = AgentObservation(
        action_type=AgentActionType.FINAL_ANSWER,
        success=True,
    )

    new_state = reducer.reduce(state, action, observation)

    assert new_state.status == "completed"
    assert len(new_state.observations) == 1
    assert new_state.observations[0].action_type == "final_answer"


def test_agent_action_accepts_null_dict_fields_from_llm() -> None:
    action = AgentAction.model_validate(
        {
            "action_type": "update_state",
            "tool_args": None,
            "state_patch": None,
            "decision_summary": "LLM returned null optional dict fields",
        }
    )

    assert action.tool_args == {}
    assert action.state_patch == {}


# ── Phase 5: validation/scoring gating tests ────────────────────────────────


def _make_candidate(plan_id: str = "plan_a"):
    from local_explorer_agent.app.domain.enums import PlanType, StageType
    from local_explorer_agent.app.domain.models import POI, PlanCandidate, Stage

    poi = POI(
        id=f"poi_{plan_id}", name=f"POI-{plan_id}", category="公园",
        city="深圳", lon=114.0, lat=22.5,
    )
    stage = Stage(
        stage_id=f"stage_{plan_id}", stage_type=StageType.EXPLORE,
        name="探索", experience_goal="开心", duration_minutes=60,
        selected_poi=poi,
    )
    return PlanCandidate(
        plan_id=plan_id, plan_type=PlanType.PLAN_A,
        title=f"方案{plan_id}", theme="亲子", stages=[stage],
    )


def test_policy_rejects_final_without_validation_when_candidates_exist() -> None:
    policy = AgentPolicy(max_steps=20, max_tool_calls=30)
    registry = ToolRegistry()
    state = _make_state(
        candidate_plans=[_make_candidate()],
        validation_result=None,
        scoring_completed=True,
    )
    action = AgentAction(
        action_type=AgentActionType.FINAL_ANSWER,
        decision_summary="done",
    )

    with pytest.raises(PolicyViolationError, match="validation_result"):
        policy.validate_action(action, state, registry)


def test_policy_rejects_final_without_scoring_when_candidates_exist() -> None:
    policy = AgentPolicy(max_steps=20, max_tool_calls=30)
    registry = ToolRegistry()
    state = _make_state(
        candidate_plans=[_make_candidate()],
        validation_result=PlanValidationResult(passed=True),
        scoring_completed=False,
    )
    action = AgentAction(
        action_type=AgentActionType.FINAL_ANSWER,
        decision_summary="done",
    )

    with pytest.raises(PolicyViolationError, match="scoring_completed"):
        policy.validate_action(action, state, registry)
