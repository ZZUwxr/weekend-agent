"""Tests for Phase 4: LLM ReAct Decider and SSE Agent Events."""

import asyncio
from datetime import datetime
from typing import TypeVar

import pytest
from pydantic import BaseModel, ValidationError

from local_explorer_agent.app.agent.react.actions import AgentAction, AgentActionType
from local_explorer_agent.app.agent.react.events import AgentEventEmitter
from local_explorer_agent.app.agent.react.factory import build_react_agent_runtime
from local_explorer_agent.app.agent.react.llm_decider import LLMReActDecider
from local_explorer_agent.app.agent.react.mock_decider import MockReActDecider
from local_explorer_agent.app.agent.react.state import AgentObservation, AgentState
from local_explorer_agent.app.agent.react.tool_registry import ToolSpec
from local_explorer_agent.app.api import deps
from local_explorer_agent.app.core.exceptions import LLMError
from local_explorer_agent.app.domain.schemas import PlanPreviewRequest, PlanPreviewStreamEvent

T = TypeVar("T", bound=BaseModel)


# ── helpers ──────────────────────────────────────────────────────────────────


def _family_request() -> PlanPreviewRequest:
    return PlanPreviewRequest(
        user_id="u001",
        query="今天下午想和老婆孩子出去玩几小时，别太远",
        city="深圳",
        start_time=datetime.fromisoformat("2026-05-10T14:00:00"),
        duration_minutes=240,
    )


def _make_state(**overrides) -> AgentState:
    base = {
        "session_id": "sess_test",
        "user_id": "u001",
        "request": _family_request(),
    }
    base.update(overrides)
    return AgentState(**base)


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


class _GarbageLLMClient:
    """LLM client that always returns unparseable output."""

    def complete_json(self, prompt: str, schema: type[T]) -> T:
        raise LLMError("Simulated LLM failure")


class _FixedActionLLMClient:
    """LLM client that always returns a fixed AgentAction."""

    def __init__(self, action: AgentAction) -> None:
        self._action = action

    def complete_json(self, prompt: str, schema: type[T]) -> T:
        if schema is AgentAction:
            return self._action  # type: ignore[return-value]
        raise LLMError(f"Unexpected schema: {schema}")


# ── 1. LLM action parser — plain JSON ───────────────────────────────────────


def test_llm_action_parser_plain_json() -> None:
    client = _FixedActionLLMClient(
        AgentAction(
            action_type=AgentActionType.FAIL,
            decision_summary="测试失败",
        )
    )
    decider = LLMReActDecider(llm_client=client, max_retries=0, allow_fallback=False)
    state = _make_state()
    tools: list[ToolSpec] = []

    action = asyncio.run(decider.decide(state, tools))

    assert action.action_type == AgentActionType.FAIL
    assert action.decision_summary == "测试失败"


# ── 2. LLM action parser — markdown JSON ────────────────────────────────────


def test_llm_action_parser_markdown_json() -> None:
    """The LLM client's complete_json already strips markdown fences.
    This test verifies the integration works end-to-end."""

    class _MarkdownLLMClient:
        """Simulates LLM returning markdown-wrapped JSON."""

        def complete_json(self, prompt: str, schema: type[T]) -> T:
            # The real OpenAI client strips markdown internally.
            # Here we simulate that by returning a valid AgentAction directly.
            return schema.model_validate({  # type: ignore[return-value]
                "action_type": "fail",
                "decision_summary": "markdown 测试",
            })

    client = _MarkdownLLMClient()
    decider = LLMReActDecider(llm_client=client, max_retries=0, allow_fallback=False)
    state = _make_state()

    action = asyncio.run(decider.decide(state, []))

    assert action.action_type == AgentActionType.FAIL
    assert action.decision_summary == "markdown 测试"


# ── 3. LLM action parser — rejects invalid schema ───────────────────────────


def test_llm_action_parser_rejects_invalid_schema() -> None:
    class _InvalidSchemaClient:
        def complete_json(self, prompt: str, schema: type[T]) -> T:
            # Return a dict missing required 'decision_summary' field
            return schema.model_validate({"action_type": "fail"})  # type: ignore[return-value]

    client = _InvalidSchemaClient()
    decider = LLMReActDecider(
        llm_client=client,
        max_retries=0,
        fallback_decider=None,
        allow_fallback=False,
    )
    state = _make_state()

    with pytest.raises(ValidationError):
        asyncio.run(decider.decide(state, []))


# ── 4. LLM decider fallback to mock on parse failure ────────────────────────


def test_llm_decider_fallback_to_mock_on_parse_failure() -> None:
    mock = MockReActDecider()
    client = _GarbageLLMClient()
    decider = LLMReActDecider(
        llm_client=client,
        max_retries=0,
        fallback_decider=mock,
        allow_fallback=True,
    )
    state = _make_state()
    tools = build_react_agent_runtime().tool_registry.list_specs()

    action = asyncio.run(decider.decide(state, tools))

    # MockReActDecider starts by reading memory before requirement intake.
    assert action.action_type == AgentActionType.CALL_TOOL
    assert action.tool_name == "read_user_memory"


# ── 5. SSE emits agent events ───────────────────────────────────────────────


def test_sse_emits_agent_events() -> None:
    events: list[PlanPreviewStreamEvent] = []

    def capture(event: PlanPreviewStreamEvent) -> None:
        events.append(event)

    emitter = AgentEventEmitter(capture)

    # Simulate emitting an action
    action = AgentAction(
        action_type=AgentActionType.CALL_TOOL,
        tool_name="understand_user",
        decision_summary="测试",
    )
    asyncio.run(emitter.emit_action(0, action))

    # Simulate emitting an observation
    obs = AgentObservation(
        action_type=AgentActionType.CALL_TOOL,
        tool_name="understand_user",
        success=True,
        data={"group_type": "family"},
    )
    asyncio.run(emitter.emit_observation(0, obs))

    event_types = [e.event for e in events]
    assert "agent_action" in event_types
    assert "step_start" in event_types
    assert "tool_observation" in event_types
    assert "step_complete" in event_types


# ── 6. SSE does not expose chain-of-thought ──────────────────────────────────


def test_sse_does_not_expose_chain_of_thought() -> None:
    events: list[PlanPreviewStreamEvent] = []

    def capture(event: PlanPreviewStreamEvent) -> None:
        events.append(event)

    emitter = AgentEventEmitter(capture)

    action = AgentAction(
        action_type=AgentActionType.CALL_TOOL,
        tool_name="understand_user",
        decision_summary="这是决策摘要",
    )
    asyncio.run(emitter.emit_action(0, action))

    for event in events:
        data = event.data
        # Must not contain reasoning or chain-of-thought keys
        assert "reasoning" not in data
        assert "chain_of_thought" not in data
        assert "hidden_reasoning" not in data
        assert "thought" not in data
        # decision_summary is allowed
        if "decision_summary" in data:
            assert data["decision_summary"] == "这是决策摘要"


# ── 7. Mock stream still works without API key ──────────────────────────────


def test_mock_stream_still_works_without_api_key(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("AGENT_RUNTIME", "react")
    _clear_all_deps_caches()

    try:
        runtime = build_react_agent_runtime()
        request = _family_request()

        events: list[PlanPreviewStreamEvent] = []

        def capture(event: PlanPreviewStreamEvent) -> None:
            events.append(event)

        emitter = AgentEventEmitter(capture)
        plan = asyncio.run(runtime.run(request, event_emitter=emitter))

        assert plan.plan_candidates
        assert plan.recommended_plan_id != ""

        event_types = [e.event for e in events]
        assert "agent_action" in event_types
        assert "tool_observation" in event_types
        assert "plan_complete" in event_types
    finally:
        _clear_all_deps_caches()
