import pytest
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


def test_api_plan_lifecycle(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("AGENT_RUNTIME", "legacy")
    _clear_all_deps_caches()

    try:
        client = TestClient(app)
        preview_payload = {
            "user_id": "u001",
            "query": "今天下午想和老婆孩子出去玩几小时，别太远，老婆最近在减肥，孩子5岁",
            "city": "深圳",
            "start_time": "2026-05-10T14:00:00",
            "duration_minutes": 240,
            "location": {"lat": 22.54, "lon": 114.05},
        }

        preview_response = client.post("/api/v1/plans/preview", json=preview_payload)
        assert preview_response.status_code == 200
        plan = preview_response.json()
        session_id = plan["session_id"]
        assert plan["recommended_plan_id"]

        get_response = client.get(f"/api/v1/plans/{session_id}")
        assert get_response.status_code == 200
        assert get_response.json()["session_id"] == session_id

        confirm_response = client.post(f"/api/v1/plans/{session_id}/confirm")
        assert confirm_response.status_code == 200
        assert confirm_response.json()["state"] == "confirmed"

        execute_response = client.post(f"/api/v1/plans/{session_id}/execute")
        assert execute_response.status_code == 200
        assert execute_response.json()["success"] is True
        assert execute_response.json()["plan"]["state"] == "completed"

        recommended = next(
            item
            for item in plan["plan_candidates"]
            if item["plan_id"] == plan["recommended_plan_id"]
        )
        affected_stage = recommended["stages"][1]
        event_payload = {
            "session_id": session_id,
            "event_type": "queue_overflow",
            "affected_poi_id": affected_stage["selected_poi"]["id"],
            "affected_stage_id": affected_stage["stage_id"],
            "severity": 4,
            "payload": {"queue_minutes": 45},
        }
        event_response = client.post(f"/api/v1/plans/{session_id}/events", json=event_payload)
        assert event_response.status_code == 200
        assert event_response.json()["plan_version"] == 2
        assert event_response.json()["state"] == "replanning"

        feedback_response = client.post(
            f"/api/v1/plans/{session_id}/feedback",
            json={"rating": 5, "raw_feedback": "整体很稳，孩子也满意", "tags": ["family"]},
        )
        assert feedback_response.status_code == 200
        assert feedback_response.json()["success"] is True

        meta_response = client.get("/api/v1/meta/schemas")
        assert meta_response.status_code == 200
        assert "RoleType" in meta_response.json()["enums"]
    finally:
        _clear_all_deps_caches()


def test_api_friends_preview(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("AGENT_RUNTIME", "legacy")
    _clear_all_deps_caches()

    try:
        client = TestClient(app)
        preview_payload = {
            "user_id": "u002",
            "query": "周末2男2女想出去玩半天，想拍照但也别太折腾，预算别太高，最好有点氛围",
            "city": "深圳",
            "start_time": "2026-05-11T14:00:00",
            "duration_minutes": 240,
            "location": {"lat": 22.54, "lon": 114.05},
        }

        response = client.post("/api/v1/plans/preview", json=preview_payload)

        assert response.status_code == 200
        plan = response.json()
        role_ids = {role["role_id"] for role in plan["inferred_context"]["roles"]}
        conflict_ids = {conflict["conflict_id"] for conflict in plan["conflicts"]}
        assert "photo_oriented_role" in role_ids
        assert "budget_sensitive_role" in role_ids
        assert "atmosphere_vs_efficiency_conflict" in conflict_ids
        assert len(plan["plan_candidates"]) == 3
    finally:
        _clear_all_deps_caches()


def test_api_plan_preview_stream_emits_sse_events(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("AGENT_RUNTIME", "legacy")
    _clear_all_deps_caches()

    try:
        client = TestClient(app)
        preview_payload = {
            "user_id": "u001",
            "query": "今天下午想和老婆孩子出去玩几小时，别太远，老婆最近在减肥，孩子5岁",
            "city": "深圳",
            "start_time": "2026-05-10T14:00:00",
            "duration_minutes": 240,
            "location": {"lat": 22.54, "lon": 114.05},
        }

        with client.stream(
            "POST",
            "/api/v1/plans/preview/stream",
            json=preview_payload,
        ) as response:
            body = "".join(response.iter_text())

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        assert "event: step_start" in body
        assert "event: step_complete" in body
        assert "event: tool_call" in body
        assert "event: candidate_start" in body
        assert "event: candidate_complete" in body
        assert "event: plan_complete" in body
        assert '"step": 5' in body
        assert '"tool": "poi_query"' in body
        assert '"tool": "poi"' in body
        assert "poi_data_empty" not in body
    finally:
        _clear_all_deps_caches()


@pytest.mark.parametrize(
    ("query", "expected_categories"),
    [
        ("晚上想和朋友吃烤肉，别太贵，环境别太吵", {"烤肉", "烧烤"}),
        ("周末晚上想看个小剧场或者脱口秀，结束后简单吃点", {"小剧场"}),
        (
            "明天下雨，想带孩子找个室内地方玩两三个小时，最好安全、少排队",
            {"亲子空间", "游乐园"},
        ),
        (
            "周日下午一家五口出去，爸妈、老婆和6岁孩子都在，"
            "孩子想玩，爸妈想少走路，老婆想吃清淡点",
            {"轻食"},
        ),
        (
            "下班后朋友想找个夜间活动，别太正式，能放松聊天，有点烟火气",
            {"烧烤", "夜间活动", "茶馆", "咖啡"},
        ),
    ],
)
def test_api_preview_keeps_strong_intent_categories(
    query: str,
    expected_categories: set[str],
    monkeypatch,
) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("AGENT_RUNTIME", "legacy")
    _clear_all_deps_caches()

    try:
        client = TestClient(app)
        preview_payload = {
            "user_id": "intent_regression",
            "query": query,
            "city": "深圳",
            "start_time": "2026-05-10T14:00:00",
            "duration_minutes": 240,
            "location": {"lat": 22.54, "lon": 114.05},
        }

        response = client.post("/api/v1/plans/preview", json=preview_payload)

        assert response.status_code == 200
        plan = response.json()
        recommended = next(
            item
            for item in plan["plan_candidates"]
            if item["plan_id"] == plan["recommended_plan_id"]
        )
        categories = {
            stage["selected_poi"]["category"]
            for stage in recommended["stages"]
            if stage.get("selected_poi")
        }
        assert expected_categories.intersection(categories)
        for stage in recommended["stages"]:
            if stage["stage_type"] == "dine" and stage.get("selected_poi"):
                assert stage["selected_poi"]["category"] in {
                    "餐厅",
                    "轻食",
                    "火锅",
                    "烧烤",
                    "烤肉",
                    "甜品",
                    "茶馆",
                    "咖啡",
                    "桑拿鸡",
                }
    finally:
        _clear_all_deps_caches()


@pytest.mark.parametrize(
    ("query", "expected_stage_type"),
    [
        ("今晚只想吃个火锅，别安排别的，环境舒服点就行", "dine"),
        ("周末只想看个展，别再拼别的行程", "explore"),
    ],
)
def test_api_preview_single_purpose_returns_one_candidate(
    query: str,
    expected_stage_type: str,
    monkeypatch,
) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("AGENT_RUNTIME", "legacy")
    _clear_all_deps_caches()

    try:
        client = TestClient(app)
        preview_payload = {
            "user_id": "single_purpose_user",
            "query": query,
            "city": "深圳",
            "start_time": "2026-05-10T19:00:00",
            "duration_minutes": 180,
            "location": {"lat": 22.54, "lon": 114.05},
        }

        response = client.post("/api/v1/plans/preview", json=preview_payload)

        assert response.status_code == 200
        plan = response.json()
        assert len(plan["plan_candidates"]) == 1
        assert plan["recommended_plan_id"] == "plan_a"

        candidate = plan["plan_candidates"][0]
        assert len(candidate["stages"]) == 1
        assert candidate["stages"][0]["stage_type"] == expected_stage_type

        task_actions = [task["action"] for task in plan["execution_graph"]]
        if expected_stage_type == "dine":
            assert task_actions == ["book_restaurant"]
        else:
            assert task_actions in ([], ["book_activity"])
    finally:
        _clear_all_deps_caches()
