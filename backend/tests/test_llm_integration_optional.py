import os

import pytest

from local_explorer_agent.app.agent.llm.openai_client import OpenAICompatibleLLMClient
from local_explorer_agent.app.domain.models import GroupContext


@pytest.mark.skipif(
    os.getenv("RUN_LLM_INTEGRATION_TEST") != "1" or not os.getenv("LLM_API_KEY"),
    reason="Set RUN_LLM_INTEGRATION_TEST=1 and LLM_API_KEY to run real LLM integration.",
)
def test_real_llm_integration_optional() -> None:
    client = OpenAICompatibleLLMClient(
        api_key=os.environ["LLM_API_KEY"],
        base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
        model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        timeout=60,
        max_retries=1,
        temperature=0.2,
        api_style="chat_completions",
        use_structured_output=True,
    )

    result = client.complete_json(
        "输出一个 family GroupContext JSON，roles 可以为空数组但必须合法。",
        GroupContext,
    )

    assert isinstance(result, GroupContext)
