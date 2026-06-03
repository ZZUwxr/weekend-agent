from pathlib import Path
from typing import Literal

from fastapi.testclient import TestClient
from pydantic import BaseModel

from local_explorer_agent.app.agent.llm.json_runner import JSONPromptRunner
from local_explorer_agent.app.api import deps
from local_explorer_agent.app.core.exceptions import LLMError
from local_explorer_agent.app.main import app


class _SimpleOutput(BaseModel):
    value: str


class _EnumOutput(BaseModel):
    value: Literal["ok"]


class _BrokenLLMClient:
    def complete_json(self, prompt: str, schema: type[BaseModel]):
        raise LLMError("invalid json from test client")


class _TimeoutLLMClient:
    def complete_json(self, prompt: str, schema: type[BaseModel]):
        raise LLMError("provider timeout api_key=tp-fake-secret-for-redaction")


class _InvalidEnumLLMClient:
    def complete_json(self, prompt: str, schema: type[BaseModel]):
        return schema.model_validate({"value": "illegal"})


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


def test_json_prompt_runner_uses_rule_based_fallback(tmp_path: Path) -> None:
    (tmp_path / "demo.md").write_text("输入：$value", encoding="utf-8")
    runner = JSONPromptRunner(
        prompt_dir=tmp_path,
        llm_client=_BrokenLLMClient(),
        max_retries=0,
    )

    output = runner.run(
        "demo.md",
        {"value": "x"},
        _SimpleOutput,
        fallback=lambda: _SimpleOutput(value="fallback"),
    )

    assert output.value == "fallback"
    assert "invalid json" in (runner.last_fallback_reason or "")


def test_json_prompt_runner_falls_back_on_timeout_and_redacts_secret(tmp_path: Path) -> None:
    (tmp_path / "demo.md").write_text("输入：$value", encoding="utf-8")
    runner = JSONPromptRunner(
        prompt_dir=tmp_path,
        llm_client=_TimeoutLLMClient(),
        max_retries=0,
    )

    output = runner.run(
        "demo.md",
        {"value": "x"},
        _SimpleOutput,
        fallback=lambda: _SimpleOutput(value="fallback"),
    )

    assert output.value == "fallback"
    assert "timeout" in (runner.last_fallback_reason or "")
    assert "tp-fake-secret-for-redaction" not in (runner.last_fallback_reason or "")
    assert "<redacted>" in (runner.last_fallback_reason or "")


def test_json_prompt_runner_falls_back_on_schema_enum_failure(tmp_path: Path) -> None:
    (tmp_path / "demo.md").write_text("输入：$value", encoding="utf-8")
    runner = JSONPromptRunner(
        prompt_dir=tmp_path,
        llm_client=_InvalidEnumLLMClient(),
        max_retries=0,
    )

    output = runner.run(
        "demo.md",
        {"value": "x"},
        _EnumOutput,
        fallback=lambda: _EnumOutput(value="ok"),
    )

    assert output.value == "ok"
    assert runner.last_fallback_reason


def test_plan_preview_does_not_crash_when_mock_llm_falls_back(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("AGENT_RUNTIME", "legacy")
    _clear_all_deps_caches()

    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/plans/preview",
            json={
                "user_id": "u001",
                "query": "今天下午想和老婆孩子出去玩几小时，别太远，老婆最近在减肥，孩子5岁",
                "city": "深圳",
                "start_time": "2026-05-10T14:00:00",
                "duration_minutes": 240,
                "location": {"lat": 22.54, "lon": 114.05},
            },
        )

        assert response.status_code == 200
        assert response.json()["recommended_plan_id"]
    finally:
        _clear_all_deps_caches()
