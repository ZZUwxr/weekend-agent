from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class AgentActionType(StrEnum):
    ASK_CLARIFICATION = "ask_clarification"
    CALL_TOOL = "call_tool"
    UPDATE_STATE = "update_state"
    DRAFT_PLAN = "draft_plan"
    VALIDATE_PLAN = "validate_plan"
    REPAIR_PLAN = "repair_plan"
    SCORE_PLAN = "score_plan"
    FINAL_ANSWER = "final_answer"
    FAIL = "fail"


class AgentAction(BaseModel):
    action_type: AgentActionType
    tool_name: str | None = None
    tool_args: dict[str, Any] = Field(default_factory=dict)
    state_patch: dict[str, Any] = Field(default_factory=dict)
    message: str | None = None
    decision_summary: str

    @field_validator("tool_args", "state_patch", mode="before")
    @classmethod
    def _empty_dict_for_null(cls, value: Any) -> Any:
        if value is None:
            return {}
        return value
