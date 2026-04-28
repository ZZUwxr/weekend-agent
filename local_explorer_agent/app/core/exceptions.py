class AppError(Exception):
    """Base application error."""


class NotFoundError(AppError):
    """Raised when a requested application resource does not exist."""


class ValidationFlowError(AppError):
    """Raised when a planner component cannot produce valid structured output."""


class LLMError(AppError):
    """Raised when an LLM client cannot produce a valid structured response."""
