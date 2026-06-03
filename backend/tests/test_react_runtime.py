"""Tests for ReAct Agent Runtime with Mock Decider."""

import asyncio
from datetime import datetime

from local_explorer_agent.app.agent.plan_manager import SessionStore
from local_explorer_agent.app.agent.react.actions import AgentAction, AgentActionType
from local_explorer_agent.app.agent.react.factory import build_react_agent_runtime
from local_explorer_agent.app.agent.react.llm_decider import LLMReActDecider
from local_explorer_agent.app.agent.react.state import AgentObservation, AgentState
from local_explorer_agent.app.api import deps
from local_explorer_agent.app.domain.enums import EventType, PlanState, PlanType, StageType
from local_explorer_agent.app.domain.memory import UserMemoryContext
from local_explorer_agent.app.domain.models import (
    ClarificationQuestion,
    ClarificationResponse,
    POI,
    GroupContext,
    PlanCandidate,
    PlanEvent,
    PlanOutput,
    Stage,
)
from local_explorer_agent.app.domain.schemas import PlanPreviewRequest
from local_explorer_agent.app.domain.validation import PlanValidationResult, PlanViolation
from local_explorer_agent.app.services.execution_service import ExecutionService


def _family_request() -> PlanPreviewRequest:
    return PlanPreviewRequest(
        user_id="u001",
        query="今天下午想和老婆孩子出去玩几小时，别太远，老婆最近在减肥，孩子5岁",
        city="深圳",
        start_time=datetime.fromisoformat("2026-05-10T14:00:00"),
        duration_minutes=240,
    )


def test_react_runtime_mock_preview_success(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    _clear_all_deps_caches()

    try:
        runtime = build_react_agent_runtime()
        request = _family_request()

        plan = asyncio.run(runtime.run(request))

        assert plan.user_id == "u001"
        assert plan.input_query == request.query
        assert plan.inferred_context is not None
        assert plan.inferred_context.group_type == "family"
        assert len(plan.plan_candidates) > 0
        assert plan.recommended_plan_id != ""
        assert plan.session_id.startswith("sess_")
    finally:
        _clear_all_deps_caches()


def _clear_all_deps_caches() -> None:
    for fn_name in (
        "get_settings",
        "get_llm_client",
        "get_json_prompt_runner",
        "get_plan_service",
        "get_orchestrator",
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


def test_mock_mode_without_api_key(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    _clear_all_deps_caches()

    try:
        service = deps.get_plan_service()
        request = _family_request()

        plan = service.preview_plan(request)

        assert plan.plan_candidates
        assert plan.recommended_plan_id
    finally:
        _clear_all_deps_caches()


def test_plan_service_uses_react_runtime_when_configured(monkeypatch) -> None:
    monkeypatch.setenv("AGENT_RUNTIME", "react")
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    _clear_all_deps_caches()

    try:
        service = deps.get_plan_service()
        assert service.react_runtime is not None
        assert service.orchestrator is None
    finally:
        _clear_all_deps_caches()


def test_openai_factory_uses_deterministic_preview_decider(monkeypatch) -> None:
    monkeypatch.setenv("AGENT_RUNTIME", "react")
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_API_KEY", "not-used-by-deterministic-preview")
    _clear_all_deps_caches()

    try:
        runtime = build_react_agent_runtime()
        request = _family_request()
        state = AgentState(
            session_id="sess_openai_factory_preview",
            user_id=request.user_id,
            request=request,
        )

        action = asyncio.run(runtime.decide_next_action(state))

        assert action.action_type == AgentActionType.CALL_TOOL
        assert action.tool_name == "read_user_memory"
    finally:
        _clear_all_deps_caches()


def test_plan_service_can_fallback_to_pipeline_runtime(monkeypatch) -> None:
    monkeypatch.setenv("AGENT_RUNTIME", "legacy")
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    _clear_all_deps_caches()

    try:
        service = deps.get_plan_service()
        assert service.orchestrator is not None
        assert service.react_runtime is None
    finally:
        _clear_all_deps_caches()


def test_api_preview_backward_compatible(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    _clear_all_deps_caches()

    try:
        runtime = build_react_agent_runtime()
        request = _family_request()

        plan = asyncio.run(runtime.run(request))

        # PlanOutput fields must all be present
        assert hasattr(plan, "session_id")
        assert hasattr(plan, "user_id")
        assert hasattr(plan, "input_query")
        assert hasattr(plan, "inferred_context")
        assert hasattr(plan, "conflicts")
        assert hasattr(plan, "negotiation_strategies")
        assert hasattr(plan, "plan_candidates")
        assert hasattr(plan, "recommended_plan_id")
        assert hasattr(plan, "execution_graph")
        assert hasattr(plan, "plan_version")
        assert hasattr(plan, "state")

        # Verify types
        assert isinstance(plan.plan_candidates, list)
        assert isinstance(plan.conflicts, list)
        assert isinstance(plan.negotiation_strategies, list)
        assert isinstance(plan.recommended_plan_id, str)
        assert plan.plan_version == 1
    finally:
        _clear_all_deps_caches()


class _PrematureFinalDecider:
    async def decide(self, state, tools):  # type: ignore[no-untyped-def]
        return AgentAction(
            action_type=AgentActionType.FINAL_ANSWER,
            decision_summary="模型提前尝试输出最终方案",
        )


def _candidate_with_selected_poi() -> PlanCandidate:
    poi = POI(
        id="poi_art_test",
        name="测试展馆",
        category="展览",
        city="深圳",
        lon=114.05,
        lat=22.55,
    )
    stage = Stage(
        stage_id="stage_art_test",
        stage_type=StageType.EXPLORE,
        name="看展",
        experience_goal="轻松看展",
        duration_minutes=120,
        selected_poi=poi,
    )
    return PlanCandidate(
        plan_id="plan_a",
        plan_type=PlanType.PLAN_A,
        title="看展方案",
        theme="展览",
        stages=[stage],
    )


def _candidate_with_dinner_and_tavern() -> PlanCandidate:
    art = Stage(
        stage_id="stage_art_test",
        stage_type=StageType.EXPLORE,
        name="看展",
        experience_goal="轻松看展",
        duration_minutes=90,
        selected_poi=POI(
            id="poi_art_test",
            name="测试展馆",
            category="展览",
            city="深圳",
            lon=114.05,
            lat=22.55,
        ),
    )
    dinner = Stage(
        stage_id="stage_dinner_test",
        stage_type=StageType.DINE,
        name="桑拿鸡晚饭",
        experience_goal="补充体力",
        duration_minutes=75,
        selected_poi=POI(
            id="poi_dinner_test",
            name="测试桑拿鸡",
            category="桑拿鸡",
            city="深圳",
            lon=114.06,
            lat=22.56,
        ),
    )
    tavern = Stage(
        stage_id="plan_a_followup_3",
        stage_type=StageType.RELAX,
        name="饭后小酒馆",
        experience_goal="饭后轻松聊天",
        duration_minutes=70,
        selected_poi=POI(
            id="poi_tavern_test",
            name="测试小酒馆",
            category="小酒馆",
            city="深圳",
            lon=114.07,
            lat=22.57,
        ),
    )
    return PlanCandidate(
        plan_id="plan_a",
        plan_type=PlanType.PLAN_A,
        title="看展加饭后小酒馆",
        theme="展览",
        stages=[art, dinner, tavern],
    )


def test_runtime_corrects_premature_final_answer(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    _clear_all_deps_caches()

    try:
        runtime = build_react_agent_runtime(
            decider=_PrematureFinalDecider(),
            max_steps=7,
        )
        request = _family_request()
        state = AgentState(
            session_id="sess_policy_recovery",
            user_id=request.user_id,
            request=request,
            goal=request.query,
            inferred_context=GroupContext(
                group_type="unknown",
                group_size=2,
                scene_label="看展",
                input_query=request.query,
            ),
            candidate_plans=[_candidate_with_selected_poi()],
        )

        plan = asyncio.run(runtime.run_from_state(state))
        trace = runtime.last_state.trace if runtime.last_state else []
        action_types = [step.action.action_type for step in trace]

        assert plan.state == PlanState.PREVIEW
        assert plan.recommended_plan_id == "plan_a"
        assert action_types == [
            AgentActionType.CALL_TOOL,
            AgentActionType.CALL_TOOL,
            AgentActionType.CALL_TOOL,
            AgentActionType.CALL_TOOL,
            AgentActionType.VALIDATE_PLAN,
            AgentActionType.SCORE_PLAN,
            AgentActionType.FINAL_ANSWER,
        ]
        assert trace[0].action.tool_name == "read_user_memory"
        assert trace[1].action.tool_name == "intake_user_requirements"
        assert trace[2].action.tool_name == "detect_conflicts"
        assert trace[3].action.tool_name == "build_timeline"
        assert all(step.action.tool_name != "generate_negotiation_strategy" for step in trace)
        assert plan.plan_candidates[0].timeline
    finally:
        _clear_all_deps_caches()


class _ShouldNotBeCalledLLM:
    def complete_json(self, prompt, schema):  # type: ignore[no-untyped-def]
        raise AssertionError("Dining revision guard should run before the LLM")


def test_llm_decider_deterministic_preview_rails_action_order(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    _clear_all_deps_caches()

    request = _family_request()
    decider = LLMReActDecider(
        _ShouldNotBeCalledLLM(),
        allow_fallback=False,
        deterministic_preview=True,
    )

    state = AgentState(
        session_id="sess_deterministic_preview",
        user_id=request.user_id,
        request=request,
    )
    first = asyncio.run(decider.decide(state, []))
    assert first.tool_name == "read_user_memory"

    state = state.model_copy(update={"user_memory": UserMemoryContext(user_id=request.user_id)})
    second = asyncio.run(decider.decide(state, []))
    assert second.tool_name == "intake_user_requirements"

    state = state.model_copy(
        update={
            "requirement_intake": None,
            "clarification_response": ClarificationResponse(
                needs_clarification=False,
                can_continue_with_assumptions=True,
            ),
        }
    )
    second_without_intake = asyncio.run(decider.decide(state, []))
    assert second_without_intake.tool_name == "intake_user_requirements"

    state = state.model_copy(
        update={
            "requirement_intake": None,
            "clarification_response": ClarificationResponse(
                needs_clarification=True,
                can_continue_with_assumptions=False,
                questions=[
                    ClarificationQuestion(
                        question_id="q_group",
                        question="几个人出门？",
                        reason="缺少同行信息",
                        required=True,
                    )
                ],
            ),
        }
    )
    still_intake_first = asyncio.run(decider.decide(state, []))
    assert still_intake_first.tool_name == "intake_user_requirements"

    from local_explorer_agent.app.domain.models import RequirementActivityCount, RequirementIntake

    state = state.model_copy(
        update={
            "requirement_intake": RequirementIntake(
                raw_query=request.query,
                primary_intent="亲子",
                activity_count=RequirementActivityCount(),
                clarification=state.clarification_response,
            )
        }
    )
    clarification = asyncio.run(decider.decide(state, []))
    assert clarification.action_type == AgentActionType.ASK_CLARIFICATION

    state = state.model_copy(
        update={
            "clarification_response": ClarificationResponse(
                needs_clarification=False,
                can_continue_with_assumptions=True,
            )
        }
    )
    understand = asyncio.run(decider.decide(state, []))
    assert understand.tool_name == "understand_user"

    state = state.model_copy(
        update={
            "inferred_context": GroupContext(input_query=request.query),
            "observations": [
                AgentObservation(
                    action_type=AgentActionType.CALL_TOOL,
                    tool_name="detect_conflicts",
                    success=True,
                    data={"conflicts": []},
                )
            ],
        }
    )
    draft = asyncio.run(decider.decide(state, []))
    assert draft.tool_name == "draft_experience_plan"

    state = state.model_copy(update={"candidate_plans": [_candidate_with_selected_poi()]})
    timeline = asyncio.run(decider.decide(state, []))
    assert timeline.tool_name == "build_timeline"

    state = state.model_copy(
        update={
            "candidate_plans": [
                _candidate_with_selected_poi().model_copy(
                    update={"timeline": [{"time": "14:00", "type": "activity", "duration_minutes": 60}]}
                )
            ]
        }
    )
    validate = asyncio.run(decider.decide(state, []))
    assert validate.action_type == AgentActionType.VALIDATE_PLAN

    state = state.model_copy(
        update={"validation_result": PlanValidationResult(passed=True)}
    )
    score = asyncio.run(decider.decide(state, []))
    assert score.action_type == AgentActionType.SCORE_PLAN

    state = state.model_copy(update={"scoring_completed": True})
    final = asyncio.run(decider.decide(state, []))
    assert final.action_type == AgentActionType.FINAL_ANSWER


def test_llm_decider_forces_dining_revision_tool(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    _clear_all_deps_caches()

    request = _family_request()
    state = AgentState(
        session_id="sess_dining_guard",
        user_id=request.user_id,
        request=request,
        is_revision=True,
        revision_instruction="再加个晚饭吧，晚饭想吃火锅",
        revision_target_plan_id="plan_a",
        candidate_plans=[_candidate_with_selected_poi()],
        recommended_plan_id="plan_a",
    )
    decider = LLMReActDecider(_ShouldNotBeCalledLLM(), allow_fallback=False)

    first = asyncio.run(decider.decide(state, []))
    assert first.tool_name == "interpret_revision_request"

    interpreted = state.model_copy(
        update={
            "revision_intents": ["add_dining", "change_dining"],
            "observations": [
                AgentObservation(
                    action_type=AgentActionType.CALL_TOOL,
                    tool_name="interpret_revision_request",
                    success=True,
                    data={"intents": ["add_dining", "change_dining"]},
                )
            ],
        }
    )
    second = asyncio.run(decider.decide(interpreted, []))

    assert second.tool_name == "revise_dining_stage"
    assert second.tool_args["cuisine_or_category"] == "火锅"
    assert second.tool_args["mode"] == "add"


def test_llm_decider_forces_dining_replacement_tool(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    _clear_all_deps_caches()

    request = _family_request()
    state = AgentState(
        session_id="sess_dining_replace_guard",
        user_id=request.user_id,
        request=request,
        is_revision=True,
        revision_instruction="把晚饭换成火锅",
        revision_target_plan_id="plan_a",
        candidate_plans=[_candidate_with_selected_poi()],
        recommended_plan_id="plan_a",
        revision_intents=["change_dining", "replace_poi"],
        observations=[
            AgentObservation(
                action_type=AgentActionType.CALL_TOOL,
                tool_name="interpret_revision_request",
                success=True,
                data={"intents": ["change_dining", "replace_poi"]},
            )
        ],
    )
    decider = LLMReActDecider(_ShouldNotBeCalledLLM(), allow_fallback=False)

    action = asyncio.run(decider.decide(state, []))

    assert action.tool_name == "revise_dining_stage"
    assert action.tool_args["cuisine_or_category"] == "火锅"
    assert action.tool_args["mode"] == "replace_or_add"


def test_llm_decider_forces_followup_stage_tool(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    _clear_all_deps_caches()

    request = _family_request()
    state = AgentState(
        session_id="sess_followup_guard",
        user_id=request.user_id,
        request=request,
        is_revision=True,
        revision_instruction="吃完饭之后安排一个小酒馆",
        revision_target_plan_id="plan_a",
        candidate_plans=[_candidate_with_selected_poi()],
        recommended_plan_id="plan_a",
        revision_intents=["add_followup_stage", "change_dining"],
        observations=[
            AgentObservation(
                action_type=AgentActionType.CALL_TOOL,
                tool_name="interpret_revision_request",
                success=True,
                data={"intents": ["add_followup_stage", "change_dining"]},
            )
        ],
    )
    decider = LLMReActDecider(_ShouldNotBeCalledLLM(), allow_fallback=False)

    action = asyncio.run(decider.decide(state, []))

    assert action.tool_name == "add_followup_stage"
    assert action.tool_args["activity_or_category"] == "小酒馆"
    assert action.tool_args["anchor"] == "after_dining"
    assert action.tool_args["mode"] == "add"


def test_llm_decider_forces_chat_before_dining_revision(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    _clear_all_deps_caches()

    request = _family_request()
    state = AgentState(
        session_id="sess_chat_before_dining_guard",
        user_id=request.user_id,
        request=request,
        is_revision=True,
        revision_instruction="在吃烧烤之前加一个适合聊天的地方",
        revision_target_plan_id="plan_a",
        candidate_plans=[_candidate_with_selected_poi()],
        recommended_plan_id="plan_a",
        revision_intents=["add_followup_stage"],
        observations=[
            AgentObservation(
                action_type=AgentActionType.CALL_TOOL,
                tool_name="interpret_revision_request",
                success=True,
                data={"intents": ["add_followup_stage"]},
            )
        ],
    )
    decider = LLMReActDecider(_ShouldNotBeCalledLLM(), allow_fallback=False)

    action = asyncio.run(decider.decide(state, []))

    assert action.tool_name == "add_followup_stage"
    assert action.tool_args["activity_or_category"] == "聊天"
    assert action.tool_args["anchor"] == "before_dining"
    assert "饭后" not in action.decision_summary


def test_llm_decider_splits_compound_dining_and_followup_revision(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    _clear_all_deps_caches()

    request = _family_request()
    state = AgentState(
        session_id="sess_compound_revision_guard",
        user_id=request.user_id,
        request=request,
        is_revision=True,
        revision_instruction="吃烧烤之后想去喝酒",
        revision_target_plan_id="plan_a",
        candidate_plans=[_candidate_with_selected_poi()],
        recommended_plan_id="plan_a",
        revision_intents=["add_followup_stage", "change_dining"],
        observations=[
            AgentObservation(
                action_type=AgentActionType.CALL_TOOL,
                tool_name="interpret_revision_request",
                success=True,
                data={"intents": ["add_followup_stage", "change_dining"]},
            )
        ],
    )
    decider = LLMReActDecider(_ShouldNotBeCalledLLM(), allow_fallback=False)

    dining_action = asyncio.run(decider.decide(state, []))
    assert dining_action.tool_name == "revise_dining_stage"
    assert dining_action.tool_args["cuisine_or_category"] == "烧烤"

    after_dining = state.model_copy(
        update={
            "observations": [
                *state.observations,
                AgentObservation(
                    action_type=AgentActionType.CALL_TOOL,
                    tool_name="revise_dining_stage",
                    success=True,
                    data={"patches": [{"patch_type": "add_dining_stage"}]},
                ),
            ]
        }
    )
    followup_action = asyncio.run(decider.decide(after_dining, []))

    assert followup_action.tool_name == "add_followup_stage"
    assert followup_action.tool_args["activity_or_category"] == "小酒馆"
    assert followup_action.tool_args["anchor"] == "after_dining"


def test_llm_decider_treats_negated_dining_category_as_exclusion(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    _clear_all_deps_caches()

    request = _family_request()
    state = AgentState(
        session_id="sess_negated_dining_guard",
        user_id=request.user_id,
        request=request,
        is_revision=True,
        revision_instruction="不想吃烧烤了",
        revision_target_plan_id="plan_a",
        candidate_plans=[_candidate_with_selected_poi()],
        recommended_plan_id="plan_a",
        revision_intents=["change_dining"],
        observations=[
            AgentObservation(
                action_type=AgentActionType.CALL_TOOL,
                tool_name="interpret_revision_request",
                success=True,
                data={"intents": ["change_dining"]},
            )
        ],
    )
    decider = LLMReActDecider(_ShouldNotBeCalledLLM(), allow_fallback=False)

    action = asyncio.run(decider.decide(state, []))

    assert action.tool_name == "revise_dining_stage"
    assert action.tool_args["cuisine_or_category"] == "餐厅"
    assert action.tool_args["message"] == "不想吃烧烤了"


def test_llm_decider_forces_cancel_followup_before_replacement(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    _clear_all_deps_caches()

    request = _family_request()
    state = AgentState(
        session_id="sess_cancel_followup_guard",
        user_id=request.user_id,
        request=request,
        is_revision=True,
        revision_instruction="不想去喝酒了，换成吃烧烤吧",
        revision_target_plan_id="plan_a",
        candidate_plans=[_candidate_with_dinner_and_tavern()],
        recommended_plan_id="plan_a",
        revision_intents=["remove_stage", "change_dining"],
        observations=[
            AgentObservation(
                action_type=AgentActionType.CALL_TOOL,
                tool_name="interpret_revision_request",
                success=True,
                data={"intents": ["remove_stage", "change_dining"]},
            )
        ],
    )
    decider = LLMReActDecider(_ShouldNotBeCalledLLM(), allow_fallback=False)

    remove_action = asyncio.run(decider.decide(state, []))
    assert remove_action.tool_name == "remove_followup_stage"
    assert remove_action.tool_args["activity_or_category"] == "小酒馆"

    after_remove = state.model_copy(
        update={
            "observations": [
                *state.observations,
                AgentObservation(
                    action_type=AgentActionType.CALL_TOOL,
                    tool_name="remove_followup_stage",
                    success=True,
                    data={"patches": [{"patch_type": "remove_followup_stage"}]},
                ),
            ]
        }
    )
    dining_action = asyncio.run(decider.decide(after_remove, []))

    assert dining_action.tool_name == "revise_dining_stage"
    assert dining_action.tool_args["cuisine_or_category"] == "烧烤"


def test_llm_decider_forces_cancel_followup_then_new_followup(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    _clear_all_deps_caches()

    request = _family_request()
    state = AgentState(
        session_id="sess_cancel_then_followup_guard",
        user_id=request.user_id,
        request=request,
        is_revision=True,
        revision_instruction="不想去喝酒了，换成喝咖啡吧",
        revision_target_plan_id="plan_a",
        candidate_plans=[_candidate_with_dinner_and_tavern()],
        recommended_plan_id="plan_a",
        revision_intents=["remove_stage", "add_followup_stage"],
        observations=[
            AgentObservation(
                action_type=AgentActionType.CALL_TOOL,
                tool_name="interpret_revision_request",
                success=True,
                data={"intents": ["remove_stage", "add_followup_stage"]},
            )
        ],
    )
    decider = LLMReActDecider(_ShouldNotBeCalledLLM(), allow_fallback=False)

    remove_action = asyncio.run(decider.decide(state, []))
    assert remove_action.tool_name == "remove_followup_stage"
    assert remove_action.tool_args["activity_or_category"] == "小酒馆"

    after_remove = state.model_copy(
        update={
            "observations": [
                *state.observations,
                AgentObservation(
                    action_type=AgentActionType.CALL_TOOL,
                    tool_name="remove_followup_stage",
                    success=True,
                    data={"patches": [{"patch_type": "remove_followup_stage"}]},
                ),
            ]
        }
    )
    followup_action = asyncio.run(decider.decide(after_remove, []))

    assert followup_action.tool_name == "add_followup_stage"
    assert followup_action.tool_args["activity_or_category"] == "咖啡"
    assert followup_action.tool_args["mode"] == "add"


def test_llm_decider_forces_cancel_followup_only(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    _clear_all_deps_caches()

    request = _family_request()
    state = AgentState(
        session_id="sess_cancel_followup_only_guard",
        user_id=request.user_id,
        request=request,
        is_revision=True,
        revision_instruction="喝酒取消呀",
        revision_target_plan_id="plan_a",
        candidate_plans=[_candidate_with_dinner_and_tavern()],
        recommended_plan_id="plan_a",
        revision_intents=["remove_stage"],
        observations=[
            AgentObservation(
                action_type=AgentActionType.CALL_TOOL,
                tool_name="interpret_revision_request",
                success=True,
                data={"intents": ["remove_stage"]},
            )
        ],
    )
    decider = LLMReActDecider(_ShouldNotBeCalledLLM(), allow_fallback=False)

    action = asyncio.run(decider.decide(state, []))

    assert action.tool_name == "remove_followup_stage"
    assert action.tool_args["activity_or_category"] == "小酒馆"


def test_llm_decider_forces_followup_replacement_tool(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    _clear_all_deps_caches()

    request = _family_request()
    state = AgentState(
        session_id="sess_followup_replace_guard",
        user_id=request.user_id,
        request=request,
        is_revision=True,
        revision_instruction="小酒馆太吵了，换一家安静点的",
        revision_target_plan_id="plan_a",
        candidate_plans=[_candidate_with_selected_poi()],
        recommended_plan_id="plan_a",
        revision_intents=[],
    )
    decider = LLMReActDecider(_ShouldNotBeCalledLLM(), allow_fallback=False)

    action = asyncio.run(decider.decide(state, []))

    assert action.tool_name == "interpret_revision_request"

    interpreted = state.model_copy(
        update={
            "observations": [
                AgentObservation(
                    action_type=AgentActionType.CALL_TOOL,
                    tool_name="interpret_revision_request",
                    success=True,
                    data={"intents": ["replace_poi"]},
                )
            ],
        }
    )
    second = asyncio.run(decider.decide(interpreted, []))

    assert second.tool_name == "add_followup_stage"
    assert second.tool_args["activity_or_category"] == "小酒馆"
    assert second.tool_args["mode"] == "replace_or_add"


def test_llm_decider_prefers_replacement_followup_category(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    _clear_all_deps_caches()

    request = _family_request()
    state = AgentState(
        session_id="sess_followup_cross_category_guard",
        user_id=request.user_id,
        request=request,
        is_revision=True,
        revision_instruction="小酒馆太吵了，换成喝咖啡吧",
        revision_target_plan_id="plan_a",
        candidate_plans=[_candidate_with_dinner_and_tavern()],
        recommended_plan_id="plan_a",
        revision_intents=[],
    )
    decider = LLMReActDecider(_ShouldNotBeCalledLLM(), allow_fallback=False)

    interpreted = state.model_copy(
        update={
            "observations": [
                AgentObservation(
                    action_type=AgentActionType.CALL_TOOL,
                    tool_name="interpret_revision_request",
                    success=True,
                    data={"intents": ["replace_poi"]},
                )
            ],
        }
    )
    action = asyncio.run(decider.decide(interpreted, []))

    assert action.tool_name == "add_followup_stage"
    assert action.tool_args["activity_or_category"] == "咖啡"
    assert action.tool_args["mode"] == "replace_or_add"


def test_llm_decider_infers_followup_stage_for_generic_place_change(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    _clear_all_deps_caches()

    request = _family_request()
    state = AgentState(
        session_id="sess_generic_followup_replace_guard",
        user_id=request.user_id,
        request=request,
        is_revision=True,
        revision_instruction="换个地方，离饭店近一点",
        revision_target_plan_id="plan_a",
        candidate_plans=[_candidate_with_dinner_and_tavern()],
        recommended_plan_id="plan_a",
        revision_intents=[],
    )
    decider = LLMReActDecider(_ShouldNotBeCalledLLM(), allow_fallback=False)

    action = asyncio.run(decider.decide(state, []))

    assert action.tool_name == "interpret_revision_request"

    interpreted = state.model_copy(
        update={
            "observations": [
                AgentObservation(
                    action_type=AgentActionType.CALL_TOOL,
                    tool_name="interpret_revision_request",
                    success=True,
                    data={"intents": ["replace_poi"]},
                )
            ],
        }
    )
    second = asyncio.run(decider.decide(interpreted, []))

    assert second.tool_name == "add_followup_stage"
    assert second.tool_args["activity_or_category"] == "小酒馆"
    assert second.tool_args["mode"] == "replace_or_add"


class _OverRepairDecider:
    async def decide(self, state, tools):  # type: ignore[no-untyped-def]
        return AgentAction(
            action_type=AgentActionType.REPAIR_PLAN,
            decision_summary="模型在修复上限后仍尝试修复",
        )


def test_runtime_turns_over_repair_into_failed_plan(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    _clear_all_deps_caches()

    try:
        runtime = build_react_agent_runtime(
            decider=_OverRepairDecider(),
            max_steps=5,
        )
        request = _family_request()
        state = AgentState(
            session_id="sess_repair_budget",
            user_id=request.user_id,
            request=request,
            goal=request.query,
            inferred_context=GroupContext(input_query=request.query),
            candidate_plans=[_candidate_with_selected_poi()],
            validation_result=PlanValidationResult(
                passed=False,
                blocking_violations=[
                    PlanViolation(
                        violation_type="closed_poi",
                        message="测试 POI 已闭店",
                        severity=5,
                        affected_plan_id="plan_a",
                    )
                ],
            ),
            repair_count=2,
        )

        plan = asyncio.run(runtime.run_from_state(state))
        trace = runtime.last_state.trace if runtime.last_state else []
        action_types = [step.action.action_type for step in trace]

        assert plan.state == PlanState.FAILED
        assert action_types == [AgentActionType.FAIL]
    finally:
        _clear_all_deps_caches()


def test_replan_queue_change_uses_react_runtime(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("AGENT_RUNTIME", "react")
    _clear_all_deps_caches()

    try:
        runtime = build_react_agent_runtime()
        request = _family_request()

        # First preview to get a plan
        original_plan = asyncio.run(runtime.run(request))
        assert original_plan.plan_candidates
        assert original_plan.plan_version == 1

        # Simulate queue overflow event
        event = PlanEvent(
            session_id=original_plan.session_id,
            event_type=EventType.QUEUE_OVERFLOW,
            affected_poi_id=original_plan.plan_candidates[0].stages[0].selected_poi.id
            if original_plan.plan_candidates[0].stages[0].selected_poi
            else None,
        )

        # Replan through runtime
        replanned = asyncio.run(runtime.run_replan(original_plan, event))

        assert replanned.session_id == original_plan.session_id
        assert replanned.plan_version == 2
        assert replanned.plan_candidates
        assert replanned.replan_reason is not None
    finally:
        _clear_all_deps_caches()


def test_execute_blocks_non_confirmed_plan() -> None:
    """ExecutionService should not execute a plan that is already executing or completed."""
    from local_explorer_agent.app.domain.models import GroupContext

    store = SessionStore()

    plan = PlanOutput(
        user_id="u001",
        input_query="test",
        inferred_context=GroupContext(),
        recommended_plan_id="p1",
        state=PlanState.EXECUTING,
    )
    saved = store.save(plan)

    class _StubTool:
        pass

    service = ExecutionService(
        session_store=store,
        booking_tool=_StubTool(),  # type: ignore[arg-type]
        taxi_tool=_StubTool(),  # type: ignore[arg-type]
        share_tool=_StubTool(),  # type: ignore[arg-type]
    )

    result = service.execute(saved.session_id)
    assert result.success is False


def test_runtime_strips_tool_name_from_ask_clarification(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    _clear_all_deps_caches()

    try:
        runtime = build_react_agent_runtime()
        request = PlanPreviewRequest(
            user_id="u001",
            query="周末出去玩一下",
            city="深圳",
            start_time=datetime.fromisoformat("2026-05-10T14:00:00"),
            duration_minutes=240,
        )
        state = AgentState(
            session_id="sess_clarify_shape",
            user_id=request.user_id,
            request=request,
            clarification_response=ClarificationResponse(
                needs_clarification=True,
                can_continue_with_assumptions=False,
                questions=[
                    ClarificationQuestion(
                        question_id="group_size",
                        question="几个人出门？",
                        reason="缺少同行人数",
                        required=True,
                    )
                ],
            ),
        )
        corrected = runtime._validate_or_correct_action(
            AgentAction(
                action_type=AgentActionType.ASK_CLARIFICATION,
                tool_name="clarify_requirements",
                message="几个人出门？",
                decision_summary="请求用户澄清",
            ),
            state,
        )

        assert corrected.action_type == AgentActionType.ASK_CLARIFICATION
        assert corrected.tool_name is None
        assert corrected.message == "几个人出门？"
    finally:
        _clear_all_deps_caches()


def test_finalize_adds_diet_warning_when_barbeque_conflicts_with_low_cal(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    _clear_all_deps_caches()

    try:
        runtime = build_react_agent_runtime()
        request = PlanPreviewRequest(
            user_id="u001",
            query="带孩子和老婆出门，老婆在减脂，想吃烧烤",
            city="深圳",
            start_time=datetime.fromisoformat("2026-05-10T19:00:00"),
            duration_minutes=240,
        )
        bbq_stage = Stage(
            stage_id="stage_bbq",
            stage_type=StageType.DINE,
            name="烧烤晚饭",
            experience_goal="朋友聚餐",
            duration_minutes=90,
            selected_poi=POI(
                id="poi_bbq",
                name="测试烧烤",
                category="烧烤",
                city="深圳",
                lon=114.05,
                lat=22.55,
            ),
        )
        candidate = PlanCandidate(
            plan_id="plan_a",
            plan_type=PlanType.PLAN_A,
            title="烧烤方案",
            theme="烧烤",
            stages=[bbq_stage],
        )
        state = AgentState(
            session_id="sess_diet_bbq",
            user_id=request.user_id,
            request=request,
            status="completed",
            inferred_context=GroupContext(
                input_query=request.query,
                inferred_constraints=["老婆在减脂"],
            ),
            candidate_plans=[candidate],
            recommended_plan_id="plan_a",
        )

        plan = runtime._finalize(state)
        text = " ".join([
            *plan.assumptions,
            plan.plan_candidates[0].tradeoff_summary,
            plan.plan_candidates[0].recommendation_reason,
        ])

        assert "减脂" in text
        assert "提醒" in text or "补偿" in text
    finally:
        _clear_all_deps_caches()


def test_finalize_surfaces_rule_fallback_without_secret(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    _clear_all_deps_caches()

    try:
        runtime = build_react_agent_runtime()
        request = PlanPreviewRequest(
            user_id="u001",
            query="今晚想吃烧烤",
            city="深圳",
            start_time=datetime.fromisoformat("2026-05-10T19:00:00"),
            duration_minutes=180,
        )
        state = AgentState(
            session_id="sess_fallback_visible",
            user_id=request.user_id,
            request=request,
            status="completed",
            inferred_context=GroupContext(input_query=request.query),
            candidate_plans=[_candidate_with_selected_poi()],
            recommended_plan_id="plan_a",
            warnings=["用户理解使用规则兜底：provider timeout api_key=<redacted>"],
        )

        plan = runtime._finalize(state)
        text = " ".join(plan.assumptions)

        assert "规则兜底" in text
        assert "校验" in text
        assert "api_key" not in text
        assert "provider timeout" not in text
    finally:
        _clear_all_deps_caches()
