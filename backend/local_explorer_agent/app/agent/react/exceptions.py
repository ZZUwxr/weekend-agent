from local_explorer_agent.app.core.exceptions import AppError


class ReActError(AppError):
    """Base error for ReAct Agent runtime."""


class ToolNotFoundError(ReActError):
    """Raised when a tool is not registered in the registry."""


class DuplicateToolError(ReActError):
    """Raised when attempting to register a tool with a name that already exists."""


class PolicyViolationError(ReActError):
    """Raised when an action violates the agent policy."""


class MaxStepsExceededError(ReActError):
    """Raised when the agent exceeds the maximum number of steps."""


class ActionParseError(ReActError):
    """Raised when the LLM output cannot be parsed into a valid AgentAction."""
