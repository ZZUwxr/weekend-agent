import asyncio
from datetime import datetime

import pytest
from pydantic import BaseModel

from local_explorer_agent.app.agent.react.actions import AgentAction, AgentActionType
from local_explorer_agent.app.agent.react.events import AgentEventEmitter
from local_explorer_agent.app.agent.react.exceptions import PolicyViolationError, ToolNotFoundError
from local_explorer_agent.app.agent.react.factory import build_react_agent_runtime
from local_explorer_agent.app.agent.react.mock_decider import MockReActDecider
from local_explorer_agent.app.agent.react.policy import AgentPolicy
from local_explorer_agent.app.agent.react.prepare_tools import (
    BookingPrepareTool,
    SharePrepareTool,
    TaxiPrepareTool,
)
from local_explorer_agent.app.agent.react.prompts import build_controller_prompt
from local_explorer_agent.app.agent.react.state import AgentObservation, AgentState
from local_explorer_agent.app.agent.react.tool_registry import ToolRegistry
from local_explorer_agent.app.api import deps
from local_explorer_agent.app.domain.enums import EventType, PlanState, PlanType, StageType
from local_explorer_agent.app.domain.models import POI, PlanCandidate, PlanEvent, Stage
from local_explorer_agent.app.domain.schemas import PlanPreviewRequest, PlanPreviewStreamEvent
from local_explorer_agent.app.domain.validation import PlanValidationResult
from local_explorer_agent.app.tools.base import ToolResult


def _request(query: str = "今天可能下雨，想带孩子去室内玩几个小时，别太远。"):
    return PlanPreviewRequest(
        user_id="u_react_contract",
        query=query,
        city="深圳",
        start_time=datetime.fromisoformat("2026-05-10T14:00:00"),
        duration_minutes=240,
    )


def _state(**overrides) -> AgentState:
    base = {
        "session_id": "sess_contract",
        "user_id": "u_react_contract",
        "request": _request(),
    }
    base.update(overrides)
    return AgentState(**base)


def _candidate(plan_id: str = "plan_a") -> PlanCandidate:
    poi = POI(
        id=f"poi_{plan_id}",
        name=f"POI {plan_id}",
        category="亲子空间",
        city="深圳",
        lon=114.0,
        lat=22.5,
        indoor=True,
        suitable_for=["儿童", "家庭"],
    )
    stage = Stage(
        stage_id=f"stage_{plan_id}",
        stage_type=StageType.EXPLORE,
        name="室内探索",
        experience_goal="亲子活动",
        duration_minutes=60,
        selected_poi=poi,
    )
    return PlanCandidate(
        plan_id=plan_id,
        plan_type=PlanType.PLAN_A,
        title="测试方案",
        theme="室内亲子",
        stages=[stage],
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


def test_tool_registry_contains_fact_and_prepare_tools(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    _clear_all_deps_caches()

    try:
        registry = build_react_agent_runtime().tool_registry
        names = {spec.name for spec in registry.list_specs()}

        assert {
            "intake_user_requirements",
            "understand_user",
            "detect_conflicts",
            "generate_negotiation_strategy",
            "draft_experience_plan",
            "select_places",
            "calculate_routes",
            "build_timeline",
            "score_candidates",
            "validate_plan_constraints",
            "repair_plan",
            "poi_search",
            "poi_detail",
            "route_search",
            "weather_lookup",
            "queue_lookup",
            "booking_prepare",
            "taxi_prepare",
            "share_prepare",
        }.issubset(names)
    finally:
        _clear_all_deps_caches()


def test_tool_registry_specs_are_unique_and_score_registered_once(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    _clear_all_deps_caches()

    try:
        specs = build_react_agent_runtime().tool_registry.list_specs()
        names = [spec.name for spec in specs]

        assert len(names) == len(set(names))
        assert names.count("score_candidates") == 1
    finally:
        _clear_all_deps_caches()


@pytest.mark.parametrize(
    ("tool", "args", "action"),
    [
        (BookingPrepareTool(), {"poi_id": "poi_1", "party_size": 3}, "book_restaurant"),
        (TaxiPrepareTool(), {"from_poi_id": "poi_1", "to_poi_id": "poi_2"}, "call_taxi"),
        (SharePrepareTool(), {"channel": "link", "recipients": []}, "share_plan"),
    ],
)
def test_prepare_tools_return_execution_task(tool, args, action) -> None:
    result = asyncio.run(tool.run(tool.args_schema.model_validate(args), _state()))

    assert result.success is True
    task = result.data["execution_task"]
    assert task["action"] == action
    assert task["requires_user_confirmation"] is True
    assert task["params"]["prepare_only"] is True


def test_policy_allows_prepare_tool_in_preview() -> None:
    registry = ToolRegistry()
    registry.register(BookingPrepareTool())
    policy = AgentPolicy(max_steps=20, max_tool_calls=30)
    action = AgentAction(
        action_type=AgentActionType.CALL_TOOL,
        tool_name="booking_prepare",
        tool_args={"poi_id": "poi_1"},
        decision_summary="prepare booking task",
    )

    policy.validate_action(action, _state(), registry)


def test_policy_rejects_unknown_tool_and_blocks_execute_tool() -> None:
    class _ExecArgs(BaseModel):
        pass

    class _ExecTool:
        name = "booking_execute"
        description = "real booking"
        args_schema = _ExecArgs
        is_execution_tool = True
        requires_confirmation = True

        async def run(self, args: BaseModel, state: AgentState) -> ToolResult:
            return ToolResult(success=True, data={})

    registry = ToolRegistry()
    registry.register(_ExecTool())
    policy = AgentPolicy(max_steps=20, max_tool_calls=30)

    with pytest.raises(ToolNotFoundError, match="not registered"):
        policy.validate_action(
            AgentAction(
                action_type=AgentActionType.CALL_TOOL,
                tool_name="missing_tool",
                decision_summary="bad",
            ),
            _state(),
            registry,
        )

    with pytest.raises(PolicyViolationError, match="not allowed during preview"):
        policy.validate_action(
            AgentAction(
                action_type=AgentActionType.CALL_TOOL,
                tool_name="booking_execute",
                decision_summary="bad",
            ),
            _state(),
            registry,
        )


def test_policy_requires_revalidate_after_repair_and_blocks_infinite_repair() -> None:
    policy = AgentPolicy(max_steps=20, max_tool_calls=30, max_repair_attempts=1)
    state = _state(
        candidate_plans=[_candidate()],
        validation_result=None,
        scoring_completed=False,
        repair_count=1,
    )

    with pytest.raises(PolicyViolationError, match="validation_result"):
        policy.validate_action(
            AgentAction(action_type=AgentActionType.FINAL_ANSWER, decision_summary="done"),
            state,
            ToolRegistry(),
        )

    with pytest.raises(PolicyViolationError, match="repair attempts"):
        policy.validate_action(
            AgentAction(action_type=AgentActionType.REPAIR_PLAN, decision_summary="repair"),
            state,
            ToolRegistry(),
        )


def test_plan_state_event_type_and_plan_type_compatibility() -> None:
    event = PlanEvent.model_validate({
        "session_id": "sess_1",
        "event_type": "queue_change",
    })
    feedback_event = PlanEvent.model_validate({
        "session_id": "sess_1",
        "event_type": "user_feedback",
    })
    legacy_candidate = _candidate().model_copy(update={"plan_type": "recommended"})
    normalized_candidate = PlanCandidate.model_validate(legacy_candidate.model_dump())

    assert event.event_type == EventType.QUEUE_OVERFLOW
    assert feedback_event.event_type == EventType.USER_PREFERENCE_CHANGE
    assert normalized_candidate.plan_type == "plan_c"
    assert PlanState.PREVIEW == "preview"


def test_llm_decider_prompt_mentions_fact_tools_and_safety_rules(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    _clear_all_deps_caches()

    try:
        specs = [
            spec.model_dump()
            for spec in build_react_agent_runtime().tool_registry.list_specs()
        ]
        prompt = build_controller_prompt(
            _state().to_llm_summary(),
            specs,
            policy_summary={"phase": "preview", "blocked_tools": ["booking_execute"]},
        )

        assert "不是固定流水线执行器" in prompt
        assert "weather_lookup" in prompt
        assert "queue_lookup" in prompt
        assert "poi_search" in prompt
        assert "route_search" in prompt
        assert "final_answer 前必须" in prompt
        assert "booking_prepare" in prompt
        assert "禁止真实执行" in prompt
    finally:
        _clear_all_deps_caches()


def test_agent_state_summary_is_compact_and_uses_recent_observations() -> None:
    state = _state(
        observations=[
            AgentObservation(
                action_type=AgentActionType.CALL_TOOL,
                tool_name=f"tool_{index}",
                success=True,
                data={"huge": "x" * 5000, "safe_key": index},
            )
            for index in range(8)
        ],
        candidate_plans=[_candidate()],
        validation_result=PlanValidationResult(passed=True),
        recommended_plan_id="plan_a",
        scoring_completed=True,
    )

    summary = state.to_llm_summary()
    as_text = str(summary)

    assert len(summary["recent_observations"]) == 5
    assert "tool_3" in as_text
    assert "tool_2" not in as_text
    assert "x" * 1000 not in as_text
    assert summary["candidates_summary"][0]["fairness_score"] == 0


class _WeatherFirstDecider:
    def __init__(self) -> None:
        self.called = False
        self.mock = MockReActDecider()

    async def decide(self, state: AgentState, tools):
        if not self.called:
            self.called = True
            return AgentAction(
                action_type=AgentActionType.CALL_TOOL,
                tool_name="weather_lookup",
                tool_args={"city": state.request.city},
                decision_summary="雨天 query 先查天气",
            )
        return await self.mock.decide(state, tools)


class _QueueBeforeFinalDecider:
    def __init__(self) -> None:
        self.called = False
        self.mock = MockReActDecider()

    async def decide(self, state: AgentState, tools):
        if not self.called and state.candidate_plans:
            first_poi = next(
                (
                    stage.selected_poi
                    for candidate in state.candidate_plans
                    for stage in candidate.stages
                    if stage.selected_poi
                ),
                None,
            )
            if first_poi is not None:
                self.called = True
                return AgentAction(
                    action_type=AgentActionType.CALL_TOOL,
                    tool_name="queue_lookup",
                    tool_args={"poi_id": first_poi.id},
                    decision_summary="热门亲子 query 在 final 前查询排队风险",
                )
        return await self.mock.decide(state, tools)


def test_react_uses_weather_lookup_for_rainy_query(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    _clear_all_deps_caches()

    try:
        runtime = build_react_agent_runtime(decider=_WeatherFirstDecider(), max_steps=25)
        events: list[PlanPreviewStreamEvent] = []
        emitter = AgentEventEmitter(events.append)

        plan = asyncio.run(runtime.run(_request(), event_emitter=emitter))
        event_types = [event.event for event in events]
        action_tools = [
            event.data.get("tool_name")
            for event in events
            if event.event == "agent_action"
        ]

        assert "weather_lookup" in action_tools
        assert "tool_observation" in event_types
        assert "score_updated" in event_types
        assert plan.state == "preview"
        assert plan.recommended_plan_id in {candidate.plan_id for candidate in plan.plan_candidates}
        recommended = next(c for c in plan.plan_candidates if c.plan_id == plan.recommended_plan_id)
        selected = [stage.selected_poi for stage in recommended.stages if stage.selected_poi]
        assert selected
        assert sum(1 for poi in selected if poi.indoor) >= 1
    finally:
        _clear_all_deps_caches()


def test_react_uses_queue_signal_for_no_wait_query(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    _clear_all_deps_caches()

    try:
        runtime = build_react_agent_runtime(decider=_QueueBeforeFinalDecider(), max_steps=25)
        events: list[PlanPreviewStreamEvent] = []
        emitter = AgentEventEmitter(events.append)
        request = _request("周末想带孩子去热门地方玩，但不想排队太久。")

        plan = asyncio.run(runtime.run(request, event_emitter=emitter))
        action_tools = [
            event.data.get("tool_name")
            for event in events
            if event.event == "agent_action"
        ]
        observations = [
            event.data
            for event in events
            if event.event == "tool_observation" and event.data.get("tool_name") == "queue_lookup"
        ]

        assert "queue_lookup" in action_tools
        assert observations
        assert plan.recommended_plan_id in {candidate.plan_id for candidate in plan.plan_candidates}
    finally:
        _clear_all_deps_caches()
