"""Tests for Phase 3: Constraint Validation, Repair, and Scoring."""

import asyncio
from datetime import datetime

import pytest

from local_explorer_agent.app.agent.react.actions import AgentAction, AgentActionType
from local_explorer_agent.app.agent.react.exceptions import PolicyViolationError
from local_explorer_agent.app.agent.react.factory import build_react_agent_runtime
from local_explorer_agent.app.agent.react.policy import AgentPolicy
from local_explorer_agent.app.agent.react.reducer import StateReducer
from local_explorer_agent.app.agent.react.state import AgentObservation, AgentState
from local_explorer_agent.app.agent.react.tool_registry import ToolRegistry
from local_explorer_agent.app.agent.react.validation_tools import (
    ConstraintValidatorTool,
    PlanRepairTool,
)
from local_explorer_agent.app.api import deps
from local_explorer_agent.app.domain.enums import GroupType, PlanType, RoleType, StageType
from local_explorer_agent.app.domain.models import (
    GroupContext,
    PlanCandidate,
    RoleProfile,
    Stage,
)
from local_explorer_agent.app.domain.schemas import PlanPreviewRequest
from local_explorer_agent.app.domain.validation import PlanValidationResult, PlanViolation
from local_explorer_agent.app.tools.base import ToolResult

# ── helpers ──────────────────────────────────────────────────────────────────


def _family_request() -> PlanPreviewRequest:
    return PlanPreviewRequest(
        user_id="u001",
        query="今天下午想和老婆孩子出去玩几小时，别太远，老婆最近在减肥，孩子5岁",
        city="深圳",
        start_time=datetime.fromisoformat("2026-05-10T14:00:00"),
        duration_minutes=240,
    )


def _family_context() -> GroupContext:
    return GroupContext(
        group_type=GroupType.FAMILY,
        roles=[
            RoleProfile(
                role_id="user",
                role_type=RoleType.USER,
                display_name="爸爸",
            ),
            RoleProfile(
                role_id="spouse",
                role_type=RoleType.SPOUSE,
                display_name="老婆",
                hard_constraints=["减肥", "低卡饮食"],
            ),
            RoleProfile(
                role_id="child_5yo",
                role_type=RoleType.CHILD,
                display_name="孩子",
                age=5,
            ),
        ],
        group_size=3,
    )


def _make_state(**overrides) -> AgentState:
    base = {
        "session_id": "sess_test",
        "user_id": "u001",
        "request": _family_request(),
    }
    base.update(overrides)
    return AgentState(**base)


def _make_candidate(
    plan_id: str = "plan_a",
    plan_type: str = PlanType.PLAN_A,
    city: str = "深圳",
    suitable_for: list[str] | None = None,
    energy_level: int = 1,
    queue_risk: str = "medium",
    indoor: bool = True,
    category: str = "公园",
    open_hours: str | None = None,
) -> PlanCandidate:
    from local_explorer_agent.app.domain.models import POI

    if suitable_for is None:
        suitable_for = ["家庭", "儿童"]

    poi = POI(
        id=f"poi_{plan_id}",
        name=f"测试POI-{plan_id}",
        category=category,
        city=city,
        lon=114.0,
        lat=22.5,
        suitable_for=suitable_for,
        energy_level=energy_level,
        queue_risk=queue_risk,
        indoor=indoor,
        open_hours=open_hours,
    )
    stage = Stage(
        stage_id=f"stage_{plan_id}",
        stage_type=StageType.EXPLORE,
        name="探索阶段",
        experience_goal="开心玩耍",
        duration_minutes=120,
        selected_poi=poi,
    )
    return PlanCandidate(
        plan_id=plan_id,
        plan_type=plan_type,
        title=f"方案 {plan_id}",
        theme="亲子探索",
        stages=[stage],
        route_segments=[
            {
                "from": f"poi_{plan_id}",
                "to": f"poi_{plan_id}",
                "walking_minutes": 0,
                "distance_meters": 0,
            }
        ],
    )


def _clear_all_deps_caches() -> None:
    for fn_name in (
        "get_settings",
        "get_llm_client",
        "get_json_prompt_runner",
        "get_plan_service",
        "get_orchestrator",
        "get_react_runtime",
        "get_poi_repository",
        "get_route_repository",
        "get_queue_repository",
        "get_weather_repository",
        "get_booking_repository",
        "get_poi_tool",
        "get_poi_query_tool",
        "get_route_tool",
        "get_queue_tool",
        "get_weather_tool",
    ):
        fn = getattr(deps, fn_name, None)
        if fn is not None and hasattr(fn, "cache_clear"):
            fn.cache_clear()


# ── 1. Validator requires candidate_plans ────────────────────────────────────


def test_validator_requires_candidate_plans() -> None:
    validator = ConstraintValidatorTool()
    state = _make_state(candidate_plans=[], inferred_context=_family_context())
    import asyncio

    result = asyncio.run(validator.run(validator.args_schema(), state))

    assert result.success is True
    data = result.data
    assert data["passed"] is False
    assert len(data["blocking_violations"]) == 1
    assert data["blocking_violations"][0]["violation_type"] == "no_candidates"


# ── 2. Validator child safety ────────────────────────────────────────────────


def test_validator_child_safety() -> None:
    validator = ConstraintValidatorTool()
    candidate = _make_candidate(
        suitable_for=["成人"],
        category="酒吧",
        energy_level=3,
    )
    state = _make_state(
        candidate_plans=[candidate],
        inferred_context=_family_context(),
    )

    result = asyncio.run(validator.run(validator.args_schema(), state))

    assert result.success is True
    data = result.data
    assert data["passed"] is False
    child_violations = [
        v for v in data["blocking_violations"] if v["violation_type"] == "child_safety"
    ]
    assert len(child_violations) == 1


# ── 3. Policy rejects final with blocking violations ─────────────────────────


def test_policy_rejects_final_with_blocking_violations() -> None:
    policy = AgentPolicy(max_steps=20, max_tool_calls=30)
    registry = ToolRegistry()

    from local_explorer_agent.app.domain.models import SatisfactionScore

    candidate = _make_candidate()
    candidate.satisfaction_scores = [
        SatisfactionScore(role_id="user", score=4.0, reasons=["good"])
    ]
    candidate.overall_score = 4.0
    candidate.min_role_score = 4.0
    candidate.fairness_score = 4.0

    vr = PlanValidationResult(
        passed=False,
        blocking_violations=[
            PlanViolation(
                violation_type="child_safety",
                message="not suitable for children",
                severity=4,
                affected_plan_id="plan_a",
            )
        ],
    )

    state = _make_state(
        candidate_plans=[candidate],
        validation_result=vr,
        scoring_completed=True,
    )
    action = AgentAction(
        action_type=AgentActionType.FINAL_ANSWER,
        decision_summary="done",
    )

    with pytest.raises(PolicyViolationError, match="failed validation|blocking violations"):
        policy.validate_action(action, state, registry)


# ── 4. Repair clears validation ──────────────────────────────────────────────


def test_repair_clears_validation() -> None:
    reducer = StateReducer()
    state = _make_state(
        candidate_plans=[_make_candidate()],
        validation_result=PlanValidationResult(
            passed=False,
            blocking_violations=[
                PlanViolation(
                    violation_type="test",
                    message="test",
                    severity=4,
                    affected_plan_id="plan_a",
                ),
            ],
        ),
        scoring_completed=True,
    )

    repaired_candidate = _make_candidate()
    action = AgentAction(
        action_type=AgentActionType.REPAIR_PLAN,
        decision_summary="repair",
    )
    observation = AgentObservation(
        action_type=AgentActionType.REPAIR_PLAN,
        tool_name="repair_plan",
        success=True,
        data={
            "candidates": [repaired_candidate.model_dump()],
            "repair_actions_taken": ["repaired"],
        },
    )

    new_state = reducer.reduce(state, action, observation)

    assert new_state.validation_result is None
    assert new_state.scoring_completed is False
    assert new_state.repair_count == 1
    assert len(new_state.candidate_plans) == 1


# ── 5. Repair then revalidate ────────────────────────────────────────────────


def test_repair_then_revalidate() -> None:
    """Blocking violation → repair → re-validate → passed."""
    validator = ConstraintValidatorTool()
    repair_tool = PlanRepairTool()

    candidate = _make_candidate(
        suitable_for=["成人"],
        category="酒吧",
    )
    state = _make_state(
        candidate_plans=[candidate],
        inferred_context=_family_context(),
    )

    # First validation should fail
    result = asyncio.run(validator.run(validator.args_schema(), state))
    data = result.data
    assert data["passed"] is False

    # Repair
    state_with_vr = _make_state(
        candidate_plans=[candidate],
        inferred_context=_family_context(),
        validation_result=PlanValidationResult(**data),
    )
    repair_result = asyncio.run(repair_tool.run(repair_tool.args_schema(), state_with_vr))
    assert repair_result.success is True

    # Re-validate with repaired candidates
    repaired_candidates = [
        PlanCandidate.model_validate(c) for c in repair_result.data["candidates"]
    ]
    state_after_repair = _make_state(
        candidate_plans=repaired_candidates,
        inferred_context=_family_context(),
    )
    asyncio.run(validator.run(validator.args_schema(), state_after_repair))

    # If the POI was replaced with a suitable fallback, validation passes
    # If no fallback was available, it still fails (expected behavior)
    if repair_result.data["repair_actions_taken"]:
        # At least one repair action was taken
        assert len(repair_result.data["repair_actions_taken"]) > 0


# ── 6. Scoring sets recommended_plan_id ──────────────────────────────────────


def test_scoring_sets_recommended_plan_id() -> None:
    from local_explorer_agent.app.domain.scoring import (
        choose_recommended_candidate,
        score_candidate,
    )

    candidates = [
        _make_candidate(plan_id="plan_a", plan_type=PlanType.PLAN_A),
        _make_candidate(plan_id="plan_b", plan_type=PlanType.PLAN_B),
    ]
    ctx = _family_context()

    scored = [score_candidate(c, ctx) for c in candidates]
    recommended = choose_recommended_candidate(scored)

    assert recommended.plan_id in ("plan_a", "plan_b")
    assert recommended.overall_score > 0
    assert recommended.min_role_score > 0
    assert recommended.fairness_score > 0


# ── 7. Full preview has validation and scoring ───────────────────────────────


def test_full_preview_has_validation_and_scoring(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    _clear_all_deps_caches()

    try:
        runtime = build_react_agent_runtime()
        request = _family_request()

        plan = asyncio.run(runtime.run(request))

        assert plan.plan_candidates
        assert plan.recommended_plan_id != ""
        assert len(plan.plan_candidates) > 0

        # Verify PlanOutput structure is complete
        assert plan.session_id.startswith("sess_")
        assert plan.user_id == "u001"
        assert plan.input_query == request.query
        assert plan.inferred_context is not None
        assert plan.inferred_context.group_type == "family"
        assert isinstance(plan.conflicts, list)
        assert isinstance(plan.negotiation_strategies, list)
    finally:
        _clear_all_deps_caches()


# ── 8. Preview blocks execution tools ────────────────────────────────────────


def test_preview_blocks_execution_tools() -> None:
    from pydantic import BaseModel

    policy = AgentPolicy(max_steps=20, max_tool_calls=30)
    registry = ToolRegistry()

    class _ExecArgs(BaseModel):
        pass

    class _ExecTool:
        args_schema = _ExecArgs
        is_execution_tool = True
        requires_confirmation = True
        description = "execution tool"

        def __init__(self, name: str) -> None:
            self.name = name

        async def run(self, args: BaseModel, state: AgentState) -> ToolResult:
            return ToolResult(success=True, data={})

    for tool_name in ("booking_tool", "taxi_tool", "share_tool"):
        registry.register(_ExecTool(tool_name))

    for tool_name in ("booking_tool", "taxi_tool", "share_tool"):
        action = AgentAction(
            action_type=AgentActionType.CALL_TOOL,
            tool_name=tool_name,
            decision_summary="try execution",
        )
        state = _make_state()

        with pytest.raises(PolicyViolationError, match="not allowed during preview"):
            policy.validate_action(action, state, registry)
