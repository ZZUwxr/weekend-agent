import logging
import re
from collections.abc import Callable
from pathlib import Path
from string import Template
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from local_explorer_agent.app.agent.llm.base import BaseLLMClient
from local_explorer_agent.app.core.exceptions import LLMError, ValidationFlowError

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)


class RuleBasedFallback:
    def complete_json(self, prompt: str, schema: type[T]) -> T:
        try:
            return schema.model_validate({})
        except ValidationError as exc:
            raise ValidationFlowError("Rule based fallback cannot build requested schema") from exc


class JSONPromptRunner:
    def __init__(
        self,
        *,
        prompt_dir: Path,
        llm_client: BaseLLMClient,
        fallback: RuleBasedFallback | None = None,
        max_retries: int = 2,
        allow_rule_based_fallback: bool = True,
    ) -> None:
        self.prompt_dir = prompt_dir
        self.llm_client = llm_client
        self.fallback = fallback or RuleBasedFallback()
        self.max_retries = max_retries
        self.allow_rule_based_fallback = allow_rule_based_fallback
        self.last_fallback_reason: str | None = None

    def run(
        self,
        prompt_name: str,
        variables: dict[str, Any],
        schema: type[T],
        fallback: Callable[[], T] | None = None,
    ) -> T:
        prompt = self._render(prompt_name, variables)
        last_error: Exception | None = None
        for _ in range(self.max_retries + 1):
            try:
                self.last_fallback_reason = None
                return self.llm_client.complete_json(prompt, schema)
            except (LLMError, ValidationError, ValueError, TypeError) as exc:
                last_error = exc
                break
        if fallback is not None and self.allow_rule_based_fallback:
            self.last_fallback_reason = self._safe_error(last_error)
            logger.warning(
                "Falling back to rule-based output for %s: %s",
                prompt_name,
                self.last_fallback_reason,
            )
            return fallback()
        if fallback is not None and last_error is not None:
            self.last_fallback_reason = self._safe_error(last_error)
            raise last_error
        try:
            return self.fallback.complete_json(prompt, schema)
        except ValidationFlowError as exc:
            if last_error:
                raise last_error from exc
            raise

    def _render(self, prompt_name: str, variables: dict[str, Any]) -> str:
        prompt_path = self.prompt_dir / prompt_name
        template = Template(prompt_path.read_text(encoding="utf-8"))
        safe_variables = {key: str(value) for key, value in variables.items()}
        return template.safe_substitute(safe_variables)

    def _safe_error(self, error: Exception | None) -> str:
        if error is None:
            return "unknown error"
        return _redact_secret_text(str(error))


def _redact_secret_text(text: str) -> str:
    patterns = (
        (re.compile(r"(?i)(api[_-]?key\s*[=:]\s*)([^\s,&]+)"), r"\1<redacted>"),
        (re.compile(r"(?i)(authorization\s*[:=]\s*)([^\s,&]+)"), r"\1<redacted>"),
        (re.compile(r"(?i)(bearer\s+)([A-Za-z0-9._-]{12,})"), r"\1<redacted>"),
        (re.compile(r"\b(sk-[A-Za-z0-9_-]{16,})\b"), "<redacted>"),
        (re.compile(r"\b(tp-[A-Za-z0-9_-]{16,})\b"), "<redacted>"),
    )
    redacted = text
    for pattern, replacement in patterns:
        redacted = pattern.sub(replacement, redacted)
    return redacted
