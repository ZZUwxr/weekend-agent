from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class FollowupModel(BaseModel):
    model_config = ConfigDict(use_enum_values=True)


class FeedbackFollowupPlace(FollowupModel):
    stage_id: str | None = None
    stage_name: str | None = None
    poi_id: str
    name: str
    category: str
    area: str | None = None


class FeedbackFollowupQuestion(FollowupModel):
    question_id: str
    question: str
    target: Literal["overall", "planning", "place"]
    poi_id: str | None = None


class FeedbackFollowupTask(FollowupModel):
    task_id: str = Field(default_factory=lambda: f"followup_{uuid4().hex[:10]}")
    session_id: str
    user_id: str
    plan_id: str
    due_at: str
    scheduled_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    status: Literal["scheduled", "sent", "completed", "cancelled"] = "scheduled"
    questions: list[FeedbackFollowupQuestion] = Field(default_factory=list)
    places: list[FeedbackFollowupPlace] = Field(default_factory=list)
    feedback_id: str | None = None
    completed_at: str | None = None
