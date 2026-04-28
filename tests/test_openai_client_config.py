import logging

import pytest

from local_explorer_agent.app.agent.llm.openai_client import OpenAICompatibleLLMClient
from local_explorer_agent.app.core.exceptions import LLMError
from local_explorer_agent.app.domain.models import GroupContext


class _FailingCompletions:
    def __init__(self, secret: str) -> None:
        self.secret = secret

    def create(self, **kwargs):
        raise RuntimeError(f"bad key {self.secret} should be hidden")


class _FakeChat:
    def __init__(self, secret: str) -> None:
        self.completions = _FailingCompletions(secret)


class _FakeOpenAI:
    def __init__(self, secret: str) -> None:
        self.chat = _FakeChat(secret)


def test_openai_client_config_and_secret_redaction(caplog: pytest.LogCaptureFixture) -> None:
    secret = "sk-test-secret"
    client = OpenAICompatibleLLMClient(
        api_key=secret,
        base_url="http://localhost:8000/v1",
        model="local-model",
        timeout=12,
        max_retries=0,
        temperature=0.1,
        api_style="chat_completions",
        use_structured_output=True,
        openai_client=_FakeOpenAI(secret),
    )

    assert client.base_url == "http://localhost:8000/v1"
    assert client.model == "local-model"
    assert client.api_key == secret

    with caplog.at_level(logging.WARNING), pytest.raises(LLMError) as exc_info:
        client.complete_json("只输出 JSON", GroupContext)

    assert secret not in str(exc_info.value)
    assert secret not in caplog.text
    assert "[REDACTED]" in caplog.text or "[REDACTED]" in str(exc_info.value)
