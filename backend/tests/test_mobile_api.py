"""Tests for mobile BFF API layer."""

from __future__ import annotations

import shutil
from pathlib import Path

from fastapi.testclient import TestClient

from local_explorer_agent.app.api import deps
from local_explorer_agent.app.api.v1.mobile import (
    _clean_revision_summary,
    _clean_revision_warnings,
)
from local_explorer_agent.app.core.exceptions import LLMError
from local_explorer_agent.app.main import app


def _clear_all_deps_caches() -> None:
    for fn_name in (
        "get_settings",
        "get_llm_client",
        "get_json_prompt_runner",
        "get_plan_service",
        "get_orchestrator",
        "get_react_runtime",
        "get_session_store",
        "get_poi_repository",
        "get_route_repository",
        "get_queue_repository",
        "get_weather_repository",
        "get_booking_repository",
        "get_user_memory_repository",
        "get_place_feedback_repository",
        "get_feedback_followup_repository",
        "get_feedback_followup_service",
        "get_memory_update_service",
        "get_mobile_state_repository",
        "get_poi_tool",
        "get_poi_query_tool",
        "get_route_tool",
        "get_queue_tool",
        "get_weather_tool",
        "get_booking_tool",
        "get_taxi_tool",
            "get_share_tool",
            "get_execution_service",
            "get_feedback_service",
            "_plan_service_for_request_llm_config",
        ):
        fn = getattr(deps, fn_name, None)
        if fn is not None and hasattr(fn, "cache_clear"):
            fn.cache_clear()


def _setup(monkeypatch) -> TestClient:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("AGENT_RUNTIME", "react")
    _clear_all_deps_caches()
    return TestClient(app)


def _copy_data_fixtures(target_dir: Path) -> None:
    source_dir = Path(__file__).resolve().parents[1] / "local_explorer_agent" / "app" / "data"
    for filename in (
        "booking_records.sample.json",
        "poi.intent_supplement.json",
        "poi.json",
        "queue_status.intent_supplement.json",
        "queue_status.json",
        "route_edges.json",
        "user_profiles.sample.json",
        "weather.sample.json",
    ):
        shutil.copy2(source_dir / filename, target_dir / filename)


def _create_session(client: TestClient) -> str:
    resp = client.post("/api/v1/mobile/travel/sessions", json={
        "message": "今天下午想和老婆孩子出去玩几小时，别太远，老婆最近在减肥，孩子5岁",
    })
    assert resp.status_code == 200
    return resp.json()["travelId"]


def _create_session_with_message(client: TestClient, message: str) -> str:
    resp = client.post("/api/v1/mobile/travel/sessions", json={"message": message})
    assert resp.status_code == 200
    return resp.json()["travelId"]


# -----------------------------------------------------------------------
# 1. Session creation
# -----------------------------------------------------------------------

def test_mobile_session_created(monkeypatch) -> None:
    client = _setup(monkeypatch)
    try:
        travel_id = _create_session(client)
        assert travel_id.startswith("sess_")
    finally:
        _clear_all_deps_caches()


def test_mobile_session_stream_emits_progress_and_travel_id(monkeypatch) -> None:
    client = _setup(monkeypatch)
    try:
        with client.stream(
            "POST",
            "/api/v1/mobile/travel/sessions/stream",
            json={
                "message": "今天下午想和老婆孩子出去玩几小时，别太远，老婆最近在减肥，孩子5岁",
            },
        ) as response:
            body = "".join(response.iter_text())

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        assert "event: agent_action" in body or "event: step_start" in body
        assert "event: plan_complete" in body
        assert "travel_id" in body or "session_id" in body
    finally:
        _clear_all_deps_caches()


# -----------------------------------------------------------------------
# 2. Conversation page
# -----------------------------------------------------------------------

def test_mobile_conversation_page(monkeypatch) -> None:
    client = _setup(monkeypatch)
    try:
        travel_id = _create_session(client)
        resp = client.get(f"/api/v1/mobile/travel/{travel_id}/conversation-page")
        assert resp.status_code == 200
        data = resp.json()
        assert data["travelId"] == travel_id
        assert len(data["statusSteps"]) > 0
        assert "clarification" in data
        assert "needsSection" in data
        assert data["needsSection"]["headerTitle"]
    finally:
        _clear_all_deps_caches()


# -----------------------------------------------------------------------
# 3. Plan comparison
# -----------------------------------------------------------------------

def test_mobile_plan_comparison(monkeypatch) -> None:
    client = _setup(monkeypatch)
    try:
        travel_id = _create_session(client)
        resp = client.get(f"/api/v1/mobile/travel/{travel_id}/plan-comparison")
        assert resp.status_code == 200
        data = resp.json()
        assert data["travelId"] == travel_id
        assert len(data["plans"]) > 0
        recommended = [p for p in data["plans"] if p.get("recommended")]
        assert len(recommended) == 1
        assert recommended[0]["recommended"] is True
    finally:
        _clear_all_deps_caches()


def test_mobile_couple_scene_does_not_generate_parent_child_content(monkeypatch) -> None:
    client = _setup(monkeypatch)
    try:
        travel_id = _create_session_with_message(
            client,
            "我们想安排一次情侣约会，帮我看看最近适合去哪、怎么安排",
        )
        resp = client.get(f"/api/v1/mobile/travel/{travel_id}/plan-comparison")
        assert resp.status_code == 200
        body = resp.text
        data = resp.json()
        assert data["travelId"] == travel_id
        assert len(data["plans"]) > 0
        assert "约会" in body or "情侣" in body
        assert "亲子" not in body
        assert "孩子" not in body
        assert "亲子空间" not in body
    finally:
        _clear_all_deps_caches()


def test_mobile_general_scene_does_not_default_to_parent_child_content(monkeypatch) -> None:
    client = _setup(monkeypatch)
    try:
        travel_id = _create_session_with_message(
            client,
            "周末想出去玩一下，轻松一点，你安排",
        )
        resp = client.get(f"/api/v1/mobile/travel/{travel_id}/plan-comparison")
        assert resp.status_code == 200
        body = resp.text
        data = resp.json()
        assert "亲子" not in body
        assert "孩子" not in body
        assert "亲子空间" not in body
        assert "一个人" not in body
        assert "独处" not in body
        assert any(
            "成人通用" in plan["headline"] or "轻活动" in plan["headline"] or "轻探索" in plan["headline"]
            for plan in data["plans"]
        )
    finally:
        _clear_all_deps_caches()


def test_mobile_plan_comparison_single_purpose_shows_one_recommendation(monkeypatch) -> None:
    client = _setup(monkeypatch)
    try:
        resp = client.post("/api/v1/mobile/travel/sessions", json={
            "message": "今晚只想吃个火锅，别安排别的",
        })
        assert resp.status_code == 200
        travel_id = resp.json()["travelId"]

        comparison = client.get(f"/api/v1/mobile/travel/{travel_id}/plan-comparison")
        assert comparison.status_code == 200
        data = comparison.json()
        assert len(data["plans"]) == 1
        assert data["plans"][0]["planLabel"] == "推荐方案"
        assert "一个" in data["topStatusText"] or "直接整理" in data["topStatusText"]

        todos = client.get(
            f"/api/v1/mobile/travel/{travel_id}/booking-todos",
            params={"planId": "plan-a"},
        )
        assert todos.status_code == 200
        todo_cards = [item for item in todos.json()["flow"] if item["type"] == "todo_card"]
        assert todo_cards
        todo_kinds = [item["kind"] for item in todo_cards[0]["card"]["items"]]
        assert "rides" not in todo_kinds
    finally:
        _clear_all_deps_caches()


# -----------------------------------------------------------------------
# 4. Plan ID hyphen normalization
# -----------------------------------------------------------------------

def test_plan_id_hyphen_normalization(monkeypatch) -> None:
    client = _setup(monkeypatch)
    try:
        travel_id = _create_session(client)
        # Try frontend camelCase query name with hyphen form.
        resp = client.get(
            f"/api/v1/mobile/travel/{travel_id}/itinerary-timeline",
            params={"planId": "plan-b"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["planId"] == "plan-b"
        assert data["planPillLabel"] == "Plan B"
        assert len(data["segments"]) > 0

        # Keep old snake_case query name working for compatibility.
        resp = client.get(
            f"/api/v1/mobile/travel/{travel_id}/itinerary-timeline",
            params={"plan_id": "plan-c"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["planId"] == "plan-c"
        assert data["planPillLabel"] == "Plan C"
    finally:
        _clear_all_deps_caches()


# -----------------------------------------------------------------------
# 5. Timeline segments
# -----------------------------------------------------------------------

def test_mobile_timeline_segments(monkeypatch) -> None:
    client = _setup(monkeypatch)
    try:
        travel_id = _create_session(client)
        resp = client.get(
            f"/api/v1/mobile/travel/{travel_id}/itinerary-timeline",
            params={"planId": "plan_a"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["segments"]) > 0
        seg = data["segments"][0]
        assert seg["scheduleLabel"]
        assert seg["title"]
        assert seg["metaLines"]
    finally:
        _clear_all_deps_caches()


# -----------------------------------------------------------------------
# 6. Booking/payment pages don't execute
# -----------------------------------------------------------------------

def test_mobile_booking_no_execute(monkeypatch) -> None:
    client = _setup(monkeypatch)
    try:
        travel_id = _create_session(client)
        # Booking todos
        resp = client.get(
            f"/api/v1/mobile/travel/{travel_id}/booking-todos",
            params={"planId": "plan_a"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["flow"]) > 0
        # The footer should mention preview
        todo_cards = [f for f in data["flow"] if f["type"] == "todo_card"]
        assert len(todo_cards) > 0
        assert "preview" in todo_cards[0]["card"]["footerBannerText"].lower()

        # Payment page
        resp = client.get(
            f"/api/v1/mobile/travel/{travel_id}/payment",
            params={"planId": "plan_a"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "预览" in data["queryBannerText"] or "preview" in data["queryBannerText"].lower()

        # Booking checkout
        resp = client.get(
            f"/api/v1/mobile/travel/{travel_id}/booking-checkout",
            params={"planId": "plan_a"},
        )
        assert resp.status_code == 200
        data = resp.json()
        tip = data["rideCard"]["tipText"]
        assert "preview" in tip.lower() or "预览" in tip

        # Confirm plan is still in preview state (not executed)
        plan_resp = client.get(f"/api/v1/plans/{travel_id}")
        assert plan_resp.status_code == 200
        assert plan_resp.json()["state"] == "preview"
    finally:
        _clear_all_deps_caches()


# -----------------------------------------------------------------------
# 7. Clarification mobile wrapper
# -----------------------------------------------------------------------

def test_mobile_clarification_wrapper(monkeypatch) -> None:
    client = _setup(monkeypatch)
    try:
        # Create a session with a vague query to trigger clarification
        resp = client.post("/api/v1/mobile/travel/sessions", json={
            "message": "周末出去玩一下",
        })
        assert resp.status_code == 200
        travel_id = resp.json()["travelId"]

        # Check if it's in clarifying state
        plan_resp = client.get(f"/api/v1/plans/{travel_id}")
        plan = plan_resp.json()

        if plan["state"] == "clarifying" and plan.get("clarification", {}).get("questions"):
            questions = plan["clarification"]["questions"]
            answers = [
                {"question_id": q["question_id"], "answer": q.get("options", ["默认"])[0] or "默认"}
                for q in questions
            ]
            clarify_resp = client.post(
                f"/api/v1/mobile/travel/{travel_id}/clarifications",
                json={"answers": answers},
            )
            assert clarify_resp.status_code == 200
            data = clarify_resp.json()
            assert data["travelId"] == travel_id
            assert "statusSteps" in data
    finally:
        _clear_all_deps_caches()


def test_mobile_conversation_page_returns_original_input_message(monkeypatch) -> None:
    client = _setup(monkeypatch)
    try:
        message = "今晚想吃烧烤"
        travel_id = _create_session_with_message(client, message)

        resp = client.get(f"/api/v1/mobile/travel/{travel_id}/conversation-page")

        assert resp.status_code == 200
        data = resp.json()
        assert data["travelId"] == travel_id
        assert data["inputMessage"] == message
    finally:
        _clear_all_deps_caches()


def test_mobile_clarification_submit_is_idempotent_after_plan_generated(monkeypatch) -> None:
    client = _setup(monkeypatch)
    try:
        travel_id = _create_session(client)

        resp = client.post(
            f"/api/v1/mobile/travel/{travel_id}/clarifications",
            json={"answers": [{"questionId": "group_size", "answer": "2人"}]},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["travelId"] == travel_id
        assert "statusSteps" in data
    finally:
        _clear_all_deps_caches()


# -----------------------------------------------------------------------
# 8. Revise mobile wrapper
# -----------------------------------------------------------------------

def test_mobile_revise_wrapper(monkeypatch) -> None:
    client = _setup(monkeypatch)
    try:
        travel_id = _create_session(client)
        resp = client.post(
            f"/api/v1/mobile/travel/{travel_id}/revise",
            json={"message": "把第一个活动换成室内项目"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["travelId"] == travel_id
        assert data["revisionSummary"]
        assert "planPage" in data
    finally:
        _clear_all_deps_caches()


def test_mobile_revision_notice_hides_internal_reason_and_validation_warning() -> None:
    summary = _clean_revision_summary(
        "已把晚饭从「B座商务烧烤」换成烧烤晚饭「蛇口二号码头边炉」。"
        "原因：根据用户修改意见，把餐饮环节调整为火锅"
    )
    warnings = _clean_revision_warnings([
        "{'violation_type': 'queue_risk', 'message': 'POI 排队风险高', "
        "'affected_plan_id': 'plan_a', 'suggested_repair_action': 'replace_poi'}",
        "没有找到可新增的咖啡地点。",
    ])

    assert "原因" not in summary
    assert "根据用户修改意见" not in summary
    assert warnings == ["没有找到可新增的咖啡地点。"]
    assert all("violation_type" not in warning for warning in warnings)


# -----------------------------------------------------------------------
# 9. Confirmed plan uses event-based mobile replan
# -----------------------------------------------------------------------

def test_confirmed_mobile_revise_uses_replan_event(monkeypatch) -> None:
    client = _setup(monkeypatch)
    try:
        travel_id = _create_session(client)
        # Confirm the plan
        confirm_resp = client.post(f"/api/v1/plans/{travel_id}/confirm")
        assert confirm_resp.status_code == 200
        assert confirm_resp.json()["state"] == "confirmed"

        # Try to revise
        revise_resp = client.post(
            f"/api/v1/mobile/travel/{travel_id}/revise",
            json={"message": "改一下"},
        )
        assert revise_resp.status_code == 200
        data = revise_resp.json()
        assert data["travelId"] == travel_id
        assert data["revisionSummary"]
        assert data["updatedPlanComparison"]
    finally:
        _clear_all_deps_caches()


# -----------------------------------------------------------------------
# 10. Static endpoints return stable DTOs
# -----------------------------------------------------------------------

def test_mobile_home_dashboard(monkeypatch) -> None:
    client = _setup(monkeypatch)
    try:
        travel_id = _create_session(client)
        resp = client.get("/api/v1/mobile/home/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert data["greetingLines"][0] == "HI~ ✨"
        assert len(data["scenes"]) == 4
        assert any(scene["variant"] == "solo" and scene["title"] == "个人出游" for scene in data["scenes"])
        assert data["companionSectionTitle"]
        assert any(option["id"] == "self" for option in data["companionOptions"])
        assert isinstance(data["history"], list)
        assert data["history"][0]["id"] == travel_id
        assert data["history"][0]["planId"]
    finally:
        _clear_all_deps_caches()


def test_mobile_user_profile(monkeypatch) -> None:
    client = _setup(monkeypatch)
    try:
        resp = client.get("/api/v1/mobile/user/profile")
        assert resp.status_code == 200
        data = resp.json()
        assert data["userName"] == ""
        assert data["archiveSectionTitle"] == "同行人出行档案"
        assert len(data["archiveTags"]) >= 2
        assert len(data["preferenceRows"]) == 4
    finally:
        _clear_all_deps_caches()


def test_mobile_companion_profile_crud(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("AGENT_RUNTIME", "react")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    _copy_data_fixtures(tmp_path)
    _clear_all_deps_caches()
    client = TestClient(app)
    headers = {"X-Device-User-Id": "companion_user"}
    try:
        listing = client.get("/api/v1/mobile/user/companions", headers=headers)
        assert listing.status_code == 200
        assert listing.json()["companions"]

        created = client.post(
            "/api/v1/mobile/user/companions",
            json={
                "displayName": "朋友A",
                "roleType": "friend",
                "softPreferences": ["咖啡", "安静聊天"],
                "riskPoints": ["太吵"],
            },
            headers=headers,
        )
        assert created.status_code == 200
        companion = created.json()["companion"]
        assert companion["displayName"] == "朋友A"
        assert companion["softPreferences"] == ["咖啡", "安静聊天"]

        updated = client.put(
            f"/api/v1/mobile/user/companions/{companion['companionId']}",
            json={
                "displayName": "朋友A",
                "roleType": "friend",
                "softPreferences": ["茶馆"],
                "riskPoints": ["太吵"],
            },
            headers=headers,
        )
        assert updated.status_code == 200
        assert updated.json()["companion"]["softPreferences"] == ["茶馆"]

        deleted = client.delete(
            f"/api/v1/mobile/user/companions/{companion['companionId']}",
            headers=headers,
        )
        assert deleted.status_code == 200
        listing = client.get("/api/v1/mobile/user/companions", headers=headers)
        assert companion["companionId"] not in [
            item["companionId"] for item in listing.json()["companions"]
        ]
    finally:
        _clear_all_deps_caches()


def test_mobile_start_session_uses_selected_companion_memory(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("AGENT_RUNTIME", "react")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    _copy_data_fixtures(tmp_path)
    _clear_all_deps_caches()
    client = TestClient(app)
    headers = {"X-Device-User-Id": "selected_companion_user"}
    try:
        created = client.post(
            "/api/v1/mobile/user/companions",
            json={
                "displayName": "朋友A",
                "roleType": "friend",
                "softPreferences": ["咖啡聊天"],
            },
            headers=headers,
        )
        assert created.status_code == 200
        companion_id = created.json()["companion"]["companionId"]

        resp = client.post(
            "/api/v1/mobile/travel/sessions",
            json={"message": "今晚出去坐坐", "companionIds": [companion_id]},
            headers=headers,
        )
        assert resp.status_code == 200
        session_id = resp.json()["travelId"]

        plan = client.get(f"/api/v1/plans/{session_id}")
        assert plan.status_code == 200
        body = plan.text
        assert "朋友A" in body
        assert "咖啡聊天" in body
    finally:
        _clear_all_deps_caches()


def test_mobile_llm_settings_are_not_persisted_on_server(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("AGENT_RUNTIME", "react")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    _copy_data_fixtures(tmp_path)
    _clear_all_deps_caches()
    client = TestClient(app)
    headers = {"X-Device-User-Id": "llm_settings_user"}
    try:
        saved = client.put(
            "/api/v1/mobile/user/settings/llm",
            json={
                "provider": "openai",
                "model": "mimo-v2.5-pro",
                "baseUrl": "https://token-plan-cn.xiaomimimo.com/v1",
                "apiKey": "tp-secret-test-key",
            },
            headers=headers,
        )
        assert saved.status_code == 200
        data = saved.json()
        assert data["ok"] is True
        assert "tp-secret-test-key" not in saved.text

        settings = client.get("/api/v1/mobile/user/settings/llm", headers=headers)
        assert settings.status_code == 200
        settings_json = settings.json()
        assert settings_json["model"] == ""
        assert settings_json["baseUrl"] == ""
        assert settings_json["apiKeyConfigured"] is False
        assert "tp-secret-test-key" not in settings.text
        saved_state = tmp_path / "runtime" / "mobile_users" / "llm_settings_user.json"
        if saved_state.exists():
            assert "tp-secret-test-key" not in saved_state.read_text(encoding="utf-8")
    finally:
        _clear_all_deps_caches()


def test_mobile_start_session_uses_request_llm_config_service(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("AGENT_RUNTIME", "react")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    _copy_data_fixtures(tmp_path)
    _clear_all_deps_caches()
    client = TestClient(app)
    headers = {"X-Device-User-Id": "saved_llm_user"}

    class _ConfiguredPlanService:
        def preview_plan(self, request, event_callback=None):  # type: ignore[no-untyped-def]
            assert request.user_id == "saved_llm_user"
            raise LLMError("OpenAI-compatible chat completion failed: 429 Too Many Requests")

    import local_explorer_agent.app.api.v1.mobile as mobile_api

    monkeypatch.setattr(
        mobile_api,
        "_plan_service_for_request_llm_config",
        lambda llm_config, default_service: _ConfiguredPlanService(),
    )

    try:
        resp = client.post(
            "/api/v1/mobile/travel/sessions",
            json={
                "message": "今晚想吃烧烤",
                "llmConfig": {
                    "provider": "openai",
                    "model": "mimo-v2.5-pro",
                    "baseUrl": "https://token-plan-cn.xiaomimimo.com/v1",
                    "apiKey": "tp-secret-test-key",
                },
            },
            headers=headers,
        )
        assert resp.status_code == 503
        assert resp.json()["code"] == "llm_rate_limited"
    finally:
        _clear_all_deps_caches()


def test_mobile_llm_settings_ignore_server_env(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_API_KEY", "tp-server-env-secret")
    monkeypatch.setenv("LLM_MODEL", "server-env-model")
    monkeypatch.setenv("LLM_BASE_URL", "https://server-env.example/v1")
    monkeypatch.setenv("AGENT_RUNTIME", "react")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    _copy_data_fixtures(tmp_path)
    _clear_all_deps_caches()
    client = TestClient(app)
    try:
        settings = client.get(
            "/api/v1/mobile/user/settings/llm",
            headers={"X-Device-User-Id": "env_isolation_user"},
        )
        assert settings.status_code == 200
        data = settings.json()
        assert data["model"] == ""
        assert data["baseUrl"] == ""
        assert data["apiKeyConfigured"] is False
        assert "tp-server-env-secret" not in settings.text
        assert "server-env-model" not in settings.text
    finally:
        _clear_all_deps_caches()


def test_mobile_travel_mode_settings(monkeypatch) -> None:
    client = _setup(monkeypatch)
    try:
        resp = client.get("/api/v1/mobile/user/preferences/travel-mode")
        assert resp.status_code == 200
        data = resp.json()
        assert data["selectedMethodId"] == "taxi"
        assert len(data["methodOptions"]) == 3
        assert data["selectedRadiusKm"] == 5
    finally:
        _clear_all_deps_caches()


def test_mobile_dietary_preferences(monkeypatch) -> None:
    client = _setup(monkeypatch)
    try:
        resp = client.get("/api/v1/mobile/user/preferences/dietary")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["needOptions"]) == 5
        assert "need-lowcal" in data["selectedNeedIds"]
        assert len(data["familyMembers"]) == 3
    finally:
        _clear_all_deps_caches()


def test_mobile_activity_preferences(monkeypatch) -> None:
    client = _setup(monkeypatch)
    try:
        resp = client.get("/api/v1/mobile/user/preferences/activity")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["tagOptions"]) == 6
        assert "tag-nature" in data["selectedTagIds"]
    finally:
        _clear_all_deps_caches()


def test_mobile_budget_pace_preferences(monkeypatch) -> None:
    client = _setup(monkeypatch)
    try:
        resp = client.get("/api/v1/mobile/user/preferences/budget-pace")
        assert resp.status_code == 200
        data = resp.json()
        assert data["selectedBudgetId"] == "budget-medium"
        assert data["selectedPaceId"] == "pace-relaxed"
        assert len(data["budgetOptions"]) == 3
        assert len(data["paceOptions"]) == 3
    finally:
        _clear_all_deps_caches()


# -----------------------------------------------------------------------
# 11. Write endpoints used by the mobile frontend
# -----------------------------------------------------------------------

def test_mobile_preference_write_endpoints(monkeypatch) -> None:
    client = _setup(monkeypatch)
    try:
        endpoints = [
            ("/api/v1/mobile/user/preferences/travel-mode", {
                "selectedMethodId": "taxi",
                "selectedRadiusKm": 5,
                "selectedDurationId": "dur-afternoon",
            }),
            ("/api/v1/mobile/user/preferences/dietary", {
                "selectedNeedIds": ["need-lowcal"],
            }),
            ("/api/v1/mobile/user/preferences/activity", {
                "selectedTagIds": ["tag-nature"],
            }),
            ("/api/v1/mobile/user/preferences/budget-pace", {
                "selectedBudgetId": "budget-medium",
                "selectedPaceId": "pace-relaxed",
            }),
        ]
        for path, payload in endpoints:
            resp = client.put(path, json=payload)
            assert resp.status_code == 200
            data = resp.json()
            assert data["ok"] is True
            assert data["updatedAt"]
    finally:
        _clear_all_deps_caches()


def test_mobile_travel_flow_write_endpoints(monkeypatch) -> None:
    client = _setup(monkeypatch)
    try:
        travel_id = _create_session(client)

        action = client.post(
            f"/api/v1/mobile/travel/{travel_id}/booking-todos/actions",
            json={"planId": "plan-a", "itemId": "rides", "action": "confirm"},
        )
        assert action.status_code == 200
        action_json = action.json()
        assert action_json["ok"] is False
        assert action_json["code"] == "provider_unavailable"

        checkout = client.post(
            f"/api/v1/mobile/travel/{travel_id}/booking-checkout/confirm",
            json={"planId": "plan-a"},
        )
        assert checkout.status_code == 200
        checkout_json = checkout.json()
        assert checkout_json["ok"] is False
        assert checkout_json["code"] == "provider_unavailable"

        order = client.post(
            f"/api/v1/mobile/travel/{travel_id}/payment/orders",
            json={"planId": "plan-a", "paymentMethodId": "wechat"},
        )
        assert order.status_code == 200
        order_json = order.json()
        assert order_json["ok"] is False
        assert order_json["code"] == "provider_unavailable"
        assert order_json["orderId"]

        complete = client.patch(
            f"/api/v1/mobile/travel/{travel_id}/payment/orders/{order_json['orderId']}/complete",
            params={"planId": "plan-a"},
        )
        assert complete.status_code == 200
        complete_json = complete.json()
        assert complete_json["ok"] is False
        assert complete_json["code"] == "provider_unavailable"
    finally:
        _clear_all_deps_caches()


def test_mobile_confirm_execute_feedback_wrappers(monkeypatch) -> None:
    client = _setup(monkeypatch)
    try:
        travel_id = _create_session(client)

        confirm = client.post(
            f"/api/v1/mobile/travel/{travel_id}/confirm",
            json={"planId": "plan-a"},
        )
        assert confirm.status_code == 200
        confirm_json = confirm.json()
        assert confirm_json["ok"] is True
        assert confirm_json["state"] == "confirmed"

        execute = client.post(
            f"/api/v1/mobile/travel/{travel_id}/execute",
            json={"planId": "plan-a"},
        )
        assert execute.status_code == 200
        execute_json = execute.json()
        assert execute_json["ok"] is False
        assert execute_json["state"] == "confirmed"
        assert execute_json["message"]
        assert isinstance(execute_json["tasks"], list)
        assert execute_json["tasks"][0]["action"] == "execute_plan"

        share = client.post(
            f"/api/v1/mobile/travel/{travel_id}/execute",
            json={"planId": "plan-a", "action": "share_itinerary"},
        )
        assert share.status_code == 200
        share_json = share.json()
        assert share_json["ok"] is False
        assert share_json["tasks"][0]["action"] == "share_itinerary"
        assert "分享" in share_json["message"]

        execute_again = client.post(
            f"/api/v1/mobile/travel/{travel_id}/execute",
            json={"planId": "plan-a"},
        )
        assert execute_again.status_code == 200
        assert execute_again.json()["ok"] is False

        feedback = client.post(
            f"/api/v1/mobile/travel/{travel_id}/feedback",
            json={
                "rating": 5,
                "rawFeedback": "安排很顺，孩子很开心",
                "tags": ["route", "rec"],
                "payload": {"planId": "plan-a"},
            },
        )
        assert feedback.status_code == 200
        feedback_json = feedback.json()
        assert feedback_json["ok"] is True
        assert feedback_json["state"] == "feedback"
        assert feedback_json["feedbackId"]
    finally:
        _clear_all_deps_caches()


def test_mobile_confirm_is_idempotent_after_execution(monkeypatch) -> None:
    client = _setup(monkeypatch)
    try:
        travel_id = _create_session(client)
        assert client.post(
            f"/api/v1/mobile/travel/{travel_id}/confirm",
            json={"planId": "plan-a"},
        ).status_code == 200
        execute = client.post(
            f"/api/v1/mobile/travel/{travel_id}/execute",
            json={"planId": "plan-a"},
        )
        assert execute.status_code == 200
        assert execute.json()["state"] == "confirmed"

        confirm_again = client.post(
            f"/api/v1/mobile/travel/{travel_id}/confirm",
            json={"planId": "plan-a"},
        )
        assert confirm_again.status_code == 200
        assert confirm_again.json()["state"] == "confirmed"
    finally:
        _clear_all_deps_caches()


def test_mobile_revise_after_execution_uses_replan_event(monkeypatch) -> None:
    client = _setup(monkeypatch)
    try:
        travel_id = _create_session(client)
        client.post(
            f"/api/v1/mobile/travel/{travel_id}/confirm",
            json={"planId": "plan-a"},
        )
        client.post(
            f"/api/v1/mobile/travel/{travel_id}/execute",
            json={"planId": "plan-a"},
        )

        revise = client.post(
            f"/api/v1/mobile/travel/{travel_id}/revise",
            json={"message": "孩子累了，后面节奏放慢一点", "targetPlanId": "plan-a"},
        )
        assert revise.status_code == 200
        data = revise.json()
        assert data["travelId"] == travel_id
        assert data["revisionSummary"]
        assert data["updatedTripLiveMap"]
        assert data["updatedItineraryHub"]
    finally:
        _clear_all_deps_caches()


# -----------------------------------------------------------------------
# Additional page DTO tests
# -----------------------------------------------------------------------

def test_mobile_payment_confirmation(monkeypatch) -> None:
    client = _setup(monkeypatch)
    try:
        travel_id = _create_session(client)
        resp = client.get(
            f"/api/v1/mobile/travel/{travel_id}/payment-confirmation",
            params={"planId": "plan_a"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["heroTitle"] == "任务已记录"
        assert "暂未接入" in data["heroSubtitle"]
        assert len(data["rows"]) > 0
        assert {row["statusKind"] for row in data["rows"]} <= {"pending_provider", "remind_later"}
        assert len(data["timelineChips"]) > 0
        assert len(data["helpActions"]) == 3
    finally:
        _clear_all_deps_caches()


def test_mobile_trip_live_map(monkeypatch) -> None:
    client = _setup(monkeypatch)
    try:
        travel_id = _create_session(client)
        resp = client.get(
            f"/api/v1/mobile/travel/{travel_id}/trip-live-map",
            params={"planId": "plan_a"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["snapshotCard"]["title"] == "行程快照"
        assert data["locationCard"]["title"] == "当前位置与下一站"
        assert data["mapImageUrl"] == "/map-empty-viewport.png"
        assert len(data["mapStops"]) > 0
        assert data["mapStops"][0]["statusText"] == "进行中"
        assert data["callRideButtonLabel"] == "叫车"
    finally:
        _clear_all_deps_caches()


def test_mobile_itinerary_hub(monkeypatch) -> None:
    client = _setup(monkeypatch)
    try:
        travel_id = _create_session(client)
        resp = client.get(
            f"/api/v1/mobile/travel/{travel_id}/itinerary-hub",
            params={"planId": "plan_a"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["navTitle"] == "行程主页"
        assert data["showNotificationsBell"] is True
        assert len(data["quickActions"]) == 5
        assert len(data["timelineNodes"]) > 0

        other_travel_id = _create_session(client)
        history_resp = client.get(
            f"/api/v1/mobile/travel/{other_travel_id}/itinerary-hub",
            params={"planId": "plan_a"},
        )
        assert history_resp.status_code == 200
        history = history_resp.json()["historyItems"]
        assert history
        assert history[0]["id"] == travel_id
        assert history[0]["planId"]
    finally:
        _clear_all_deps_caches()


def test_mobile_page_read_updates_active_travel(monkeypatch) -> None:
    client = _setup(monkeypatch)
    try:
        first_travel_id = _create_session(client)
        second_travel_id = _create_session(client)

        active = client.get("/api/v1/mobile/travel/active")
        assert active.status_code == 200
        assert active.json()["travelId"] == second_travel_id

        timeline = client.get(
            f"/api/v1/mobile/travel/{first_travel_id}/itinerary-timeline",
            params={"planId": "plan-b"},
        )
        assert timeline.status_code == 200

        active = client.get("/api/v1/mobile/travel/active")
        assert active.status_code == 200
        data = active.json()
        assert data["travelId"] == first_travel_id
        assert data["planId"] == "plan-b"
    finally:
        _clear_all_deps_caches()


def test_mobile_nonexistent_session_returns_404(monkeypatch) -> None:
    client = _setup(monkeypatch)
    try:
        resp = client.get("/api/v1/mobile/travel/nonexistent/conversation-page")
        assert resp.status_code == 404
    finally:
        _clear_all_deps_caches()


def test_mobile_invalid_device_user_id_returns_normalized_400(monkeypatch) -> None:
    client = _setup(monkeypatch)
    try:
        resp = client.get(
            "/api/v1/mobile/home/dashboard",
            headers={"X-Device-User-Id": "../bad"},
        )
        assert resp.status_code == 400
        data = resp.json()
        assert data["code"] == "invalid_device_user_id"
        assert data["message"]
        assert data["details"]["header"] == "X-Device-User-Id"
    finally:
        _clear_all_deps_caches()


def test_mobile_llm_rate_limit_returns_normalized_error(monkeypatch) -> None:
    class _RateLimitedPlanService:
        def preview_plan(self, request):  # type: ignore[no-untyped-def]
            raise LLMError("OpenAI-compatible chat completion failed: 429 Too Many Requests")

    client = _setup(monkeypatch)
    import local_explorer_agent.app.api.v1.mobile as mobile_api

    monkeypatch.setattr(
        mobile_api,
        "_plan_service_for_request_llm_config",
        lambda llm_config, default_service: _RateLimitedPlanService(),
    )
    try:
        resp = client.post(
            "/api/v1/mobile/travel/sessions",
            json={
                "message": "今晚想吃烧烤",
                "llmConfig": {
                    "provider": "openai",
                    "model": "mimo-v2.5-pro",
                    "baseUrl": "https://token-plan-cn.xiaomimimo.com/v1",
                    "apiKey": "tp-secret-test-key",
                },
            },
        )

        assert resp.status_code == 503
        data = resp.json()
        assert data == {
            "code": "llm_rate_limited",
            "message": "AI 服务繁忙，请稍后再试。",
            "details": {"provider": "openai_compatible"},
        }
    finally:
        _clear_all_deps_caches()


def test_mobile_feedback_memory_loop_surfaces_history_preference(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("AGENT_RUNTIME", "react")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    _copy_data_fixtures(tmp_path)
    _clear_all_deps_caches()
    client = TestClient(app)
    headers = {"X-Device-User-Id": "memory_loop_user"}

    try:
        first = client.post(
            "/api/v1/mobile/travel/sessions",
            json={"message": "找个书店待一会儿"},
            headers=headers,
        )
        assert first.status_code == 200
        travel_id = first.json()["travelId"]

        feedback = client.post(
            f"/api/v1/mobile/travel/{travel_id}/feedback",
            json={
                "rating": 2,
                "rawFeedback": "这个书店太吵了",
                "tags": ["too_noisy"],
            },
            headers=headers,
        )
        assert feedback.status_code == 200
        assert feedback.json()["ok"] is True

        memory = client.get(
            "/api/v1/users/memory_loop_user/memory",
            headers=headers,
        )
        assert memory.status_code == 200
        memory_json = memory.json()
        assert memory_json["category_weights"]["书店"] < 1
        assert memory_json["tag_weights"]["热闹"] < 1
        assert memory_json["disliked_poi_ids"]

        second = client.post(
            "/api/v1/mobile/travel/sessions",
            json={"message": "今晚想出去坐坐聊天"},
            headers=headers,
        )
        assert second.status_code == 200
        second_travel_id = second.json()["travelId"]

        comparison = client.get(
            f"/api/v1/mobile/travel/{second_travel_id}/plan-comparison",
            headers=headers,
        )
        assert comparison.status_code == 200
        comparison_json = comparison.json()
        text = comparison_json["assistantMessage"]
        assert "历史偏好" in text
        assert "当前输入中的明确要求优先" in text
    finally:
        _clear_all_deps_caches()
