import json
import logging
import re
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from local_explorer_agent.app.core.exceptions import LLMError

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)


class OpenAICompatibleLLMClient:
    def __init__(
        self,
        *,
        api_key: str | None,
        base_url: str,
        model: str,
        timeout: float,
        max_retries: int,
        temperature: float,
        api_style: str,
        use_structured_output: bool,
        trust_env: bool = False,
        openai_client: Any | None = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.temperature = temperature
        self.api_style = api_style
        self.use_structured_output = use_structured_output
        self.trust_env = trust_env
        self._client = openai_client

    def complete_json(self, prompt: str, schema: type[T]) -> T:
        if not self.api_key:
            raise LLMError("LLM_API_KEY is empty while LLM_PROVIDER=openai")
        if self.api_style == "responses":
            raise LLMError("Responses API style is reserved for future implementation")
        if self.api_style != "chat_completions":
            raise LLMError(f"Unsupported LLM_API_STYLE: {self.api_style}")

        current_prompt = self._with_json_contract(prompt, schema)
        last_error: Exception | None = None
        last_output = ""
        for attempt in range(self.max_retries + 1):
            try:
                raw_output = self._chat_complete(current_prompt, schema)
                last_output = raw_output
                payload = json.loads(self._extract_json_text(raw_output))
                return schema.model_validate(payload)
            except (json.JSONDecodeError, ValidationError, LLMError) as exc:
                last_error = exc
                logger.warning(
                    "LLM structured output attempt %s failed for schema %s: %s",
                    attempt + 1,
                    schema.__name__,
                    self._safe_error(exc),
                )
                if isinstance(exc, LLMError) and self._is_terminal_provider_error(exc):
                    break
                current_prompt = self._repair_prompt(
                    original_prompt=prompt,
                    invalid_output=last_output,
                    error=exc,
                    schema=schema,
                )
        raise LLMError(
            f"LLM failed to produce valid JSON for schema {schema.__name__}: "
            f"{self._safe_error(last_error)}"
        )

    def _client_instance(self) -> Any:
        if self._client is not None:
            return self._client
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise LLMError("openai package is not installed") from exc
        self._client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
            # Keep retries under this module's control. If the SDK also retries,
            # one logical schema repair attempt becomes response_formats * SDK retries.
            max_retries=0,
            http_client=httpx.Client(timeout=self.timeout, trust_env=self.trust_env),
        )
        return self._client

    def _chat_complete(self, prompt: str, schema: type[BaseModel]) -> str:
        formats: list[dict[str, Any] | None] = []
        if self.use_structured_output:
            formats.append(self._json_schema_response_format(schema))
        formats.extend([{"type": "json_object"}, None])

        last_error: Exception | None = None
        for response_format in formats:
            try:
                kwargs: dict[str, Any] = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "你是严格 JSON/json 输出的 Agent 决策模块，"
                                "只返回合法 json。"
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": self.temperature,
                }
                if response_format is not None:
                    kwargs["response_format"] = response_format
                response = self._client_instance().chat.completions.create(**kwargs)
                content = self._extract_message_content(response)
                if not content:
                    raise LLMError("OpenAI-compatible response content is empty")
                return content
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                logger.warning(
                    "OpenAI-compatible call failed with response_format=%s: %s",
                    self._format_name(response_format),
                    self._safe_error(exc),
                )
                if self._is_terminal_provider_error(exc):
                    break
        raise LLMError(f"OpenAI-compatible chat completion failed: {self._safe_error(last_error)}")

    def _json_schema_response_format(self, schema: type[BaseModel]) -> dict[str, Any]:
        schema_name = re.sub(r"[^a-zA-Z0-9_]", "_", schema.__name__)[:64] or "StructuredOutput"
        return {
            "type": "json_schema",
            "json_schema": {
                "name": schema_name,
                "schema": schema.model_json_schema(),
                "strict": True,
            },
        }

    def _extract_message_content(self, response: Any) -> str:
        if isinstance(response, dict):
            return str(response["choices"][0]["message"]["content"])
        choices = getattr(response, "choices", [])
        if not choices:
            return ""
        message = getattr(choices[0], "message", None)
        return str(getattr(message, "content", "") or "")

    def _extract_json_text(self, raw_output: str) -> str:
        text = raw_output.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
            text = re.sub(r"```$", "", text).strip()
        if text.startswith("{") or text.startswith("["):
            return text
        object_index = text.find("{")
        array_index = text.find("[")
        candidates = [index for index in [object_index, array_index] if index >= 0]
        return text[min(candidates) :] if candidates else text

    def _with_json_contract(self, prompt: str, schema: type[BaseModel]) -> str:
        return (
            f"{prompt}\n\n"
            "严格要求：只能输出一个合法 JSON；不要 Markdown；不要代码块；不要解释文字。\n"
            f"目标 JSON Schema：\n{json.dumps(schema.model_json_schema(), ensure_ascii=False)}"
        )

    def _repair_prompt(
        self,
        *,
        original_prompt: str,
        invalid_output: str,
        error: Exception,
        schema: type[BaseModel],
    ) -> str:
        return (
            f"{original_prompt}\n\n"
            "上一次输出无法通过 JSON/Pydantic 校验。请修复并只返回合法 JSON。\n"
            f"错误信息：{self._safe_error(error)}\n"
            f"非法输出：{invalid_output[:4000]}\n"
            f"目标 JSON Schema：{json.dumps(schema.model_json_schema(), ensure_ascii=False)}"
        )

    def _safe_error(self, error: Exception | None) -> str:
        if error is None:
            return "unknown error"
        message = str(error)
        if self.api_key:
            message = message.replace(self.api_key, "[REDACTED]")
        return message

    def _format_name(self, response_format: dict[str, Any] | None) -> str:
        if response_format is None:
            return "plain_prompt"
        return str(response_format.get("type", "unknown"))

    def _is_timeout_like(self, error: Exception) -> bool:
        error_name = error.__class__.__name__.lower()
        message = str(error).lower()
        return any(
            marker in error_name or marker in message
            for marker in ("timeout", "timed out", "readtimeout", "connecttimeout")
        )

    def _is_rate_limit_like(self, error: Exception) -> bool:
        error_name = error.__class__.__name__.lower()
        message = str(error).lower()
        return any(
            marker in error_name or marker in message
            for marker in ("429", "rate limit", "ratelimit", "too many requests")
        )

    def _is_terminal_provider_error(self, error: Exception) -> bool:
        return self._is_timeout_like(error) or self._is_rate_limit_like(error)
