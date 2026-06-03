from fastapi.testclient import TestClient

from local_explorer_agent.app.api import deps
from local_explorer_agent.app.main import app


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
        "get_execution_service",
        "get_feedback_service",
    ):
        fn = getattr(deps, fn_name, None)
        if fn is not None and hasattr(fn, "cache_clear"):
            fn.cache_clear()


def test_family_and_friends_preview_with_default_mock_llm(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("AGENT_RUNTIME", "legacy")
    _clear_all_deps_caches()

    try:
        client = TestClient(app)
        payloads = [
            {
                "user_id": "u001",
                "query": "今天下午想和老婆孩子出去玩几小时，别太远，老婆最近在减肥，孩子5岁",
                "city": "深圳",
                "start_time": "2026-05-10T14:00:00",
                "duration_minutes": 240,
                "location": {"lat": 22.54, "lon": 114.05},
            },
            {
                "user_id": "u002",
                "query": "周末2男2女想出去玩半天，想拍照但也别太折腾，预算别太高，最好有点氛围",
                "city": "深圳",
                "start_time": "2026-05-11T14:00:00",
                "duration_minutes": 240,
                "location": {"lat": 22.54, "lon": 114.05},
            },
        ]

        for payload in payloads:
            response = client.post("/api/v1/plans/preview", json=payload)
            assert response.status_code == 200
            body = response.json()
            assert body["recommended_plan_id"]
            assert len(body["plan_candidates"]) == 3
    finally:
        _clear_all_deps_caches()
