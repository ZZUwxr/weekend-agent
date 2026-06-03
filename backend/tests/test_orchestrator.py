from datetime import datetime

from local_explorer_agent.app.api import deps
from local_explorer_agent.app.api.deps import get_plan_service
from local_explorer_agent.app.domain.schemas import Location, PlanPreviewRequest


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


def test_orchestrator_preview_plan_output(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("AGENT_RUNTIME", "legacy")
    _clear_all_deps_caches()

    try:
        service = get_plan_service()
        request = PlanPreviewRequest(
            user_id="u001",
            query="今天下午想和老婆孩子出去玩几小时，别太远，老婆最近在减肥，孩子5岁",
            city="深圳",
            start_time=datetime.fromisoformat("2026-05-10T14:00:00"),
            duration_minutes=240,
            location=Location(lat=22.54, lon=114.05),
        )

        plan = service.preview_plan(request)

        assert plan.session_id
        assert len(plan.plan_candidates) == 3
        assert {candidate.plan_type for candidate in plan.plan_candidates} == {
            "plan_a",
            "plan_b",
            "plan_c",
        }
        assert plan.recommended_plan_id
        assert plan.execution_graph
        recommended = next(
            candidate
            for candidate in plan.plan_candidates
            if candidate.plan_id == plan.recommended_plan_id
        )
        assert recommended.timeline
        assert recommended.min_role_score >= 3.5
        assert recommended.fairness_score >= 4.0
        assert "不是简单平均分最高" in recommended.recommendation_reason
    finally:
        _clear_all_deps_caches()


def test_orchestrator_friends_preview_plan_output(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("AGENT_RUNTIME", "legacy")
    _clear_all_deps_caches()

    try:
        service = get_plan_service()
        request = PlanPreviewRequest(
            user_id="u002",
            query="周末2男2女想出去玩半天，想拍照但也别太折腾，预算别太高，最好有点氛围",
            city="深圳",
            start_time=datetime.fromisoformat("2026-05-11T14:00:00"),
            duration_minutes=240,
            location=Location(lat=22.54, lon=114.05),
        )

        plan = service.preview_plan(request)
        role_ids = {role.role_id for role in plan.inferred_context.roles}
        conflict_ids = {conflict.conflict_id for conflict in plan.conflicts}

        assert {
            "photo_oriented_role",
            "practical_oriented_role",
            "budget_sensitive_role",
        }.issubset(role_ids)
        assert "atmosphere_vs_efficiency_conflict" in conflict_ids
        assert len(plan.plan_candidates) == 3
        assert all(2 <= len(candidate.stages) <= 4 for candidate in plan.plan_candidates)
        recommended = next(
            candidate
            for candidate in plan.plan_candidates
            if candidate.plan_id == plan.recommended_plan_id
        )
        assert "不是简单平均分最高" in recommended.recommendation_reason
        assert recommended.model_validate(recommended.model_dump())
    finally:
        _clear_all_deps_caches()
