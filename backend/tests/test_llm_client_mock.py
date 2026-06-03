from local_explorer_agent.app.agent.llm.mock_client import MockLLMClient
from local_explorer_agent.app.api import deps
from local_explorer_agent.app.core.config import get_settings
from local_explorer_agent.app.domain.models import GroupContext


def test_default_config_uses_mock_llm_client(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    get_settings.cache_clear()
    deps.get_llm_client.cache_clear()

    client = deps.get_llm_client()

    assert isinstance(client, MockLLMClient)
    result = client.complete_json("普通家庭 demo", GroupContext)
    assert isinstance(result, GroupContext)
    assert result.group_type == "family"
