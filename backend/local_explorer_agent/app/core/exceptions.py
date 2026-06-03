class AppError(Exception):
    """Base application error."""


class NotFoundError(AppError):
    """Raised when a requested application resource does not exist."""


class ValidationFlowError(AppError):
    """Raised when a planner component cannot produce valid structured output."""


class LLMError(AppError):
    """Raised when an LLM client cannot produce a valid structured response."""


def classify_llm_error(exc: Exception) -> tuple[int, str, str]:
    """Map provider failures to normalized API status/code/message."""
    text = str(exc).lower()
    name = exc.__class__.__name__.lower()
    if any(marker in text or marker in name for marker in ("429", "rate limit", "too many requests")):
        return 503, "llm_rate_limited", "AI 服务繁忙，请稍后再试。"
    if any(marker in text or marker in name for marker in ("timeout", "timed out", "readtimeout", "connecttimeout")):
        return 504, "llm_timeout", "AI 服务响应超时，请稍后重试。"
    if any(marker in text for marker in ("json", "validation", "schema", "structured output")):
        return 502, "llm_invalid_response", "AI 返回内容暂时无法解析，请重试。"
    return 503, "llm_unavailable", "AI 服务暂不可用，请稍后再试。"
