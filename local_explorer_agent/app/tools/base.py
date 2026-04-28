import time
from typing import Any

from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    success: bool
    data: Any = None
    error_code: str | None = None
    error_message: str | None = None
    latency_ms: int = Field(default=0, ge=0)
    mock_scenario: str = "success"


class BaseTool:
    name: str = "base_tool"

    def _result(
        self,
        *,
        success: bool = True,
        data: Any = None,
        error_code: str | None = None,
        error_message: str | None = None,
        started_at: float | None = None,
        mock_scenario: str = "success",
    ) -> ToolResult:
        latency_ms = int((time.perf_counter() - started_at) * 1000) if started_at else 0
        return ToolResult(
            success=success,
            data=data,
            error_code=error_code,
            error_message=error_message,
            latency_ms=latency_ms,
            mock_scenario=mock_scenario,
        )
