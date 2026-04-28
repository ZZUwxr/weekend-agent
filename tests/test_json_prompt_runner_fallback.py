from pathlib import Path

from fastapi.testclient import TestClient
from pydantic import BaseModel

from local_explorer_agent.app.agent.llm.json_runner import JSONPromptRunner
from local_explorer_agent.app.core.exceptions import LLMError
from local_explorer_agent.app.main import app


class _SimpleOutput(BaseModel):
    value: str


class _BrokenLLMClient:
    def complete_json(self, prompt: str, schema: type[BaseModel]):
        raise LLMError("invalid json from test client")


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


def test_plan_preview_does_not_crash_when_mock_llm_falls_back() -> None:
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
