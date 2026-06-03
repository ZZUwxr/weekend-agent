from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from local_explorer_agent.app.domain.enums import (
    ConflictType,
    EventType,
    ExecutionAction,
    GroupType,
    PlanState,
    PlanType,
    RoleType,
    StageType,
    StrategyType,
)
from local_explorer_agent.app.domain.followup import FeedbackFollowupTask
from local_explorer_agent.app.domain.models import (
    ExecutionTask,
    PlanOutput,
    PlanRevisionSummary,
)


class SchemaModel(BaseModel):
    model_config = ConfigDict(use_enum_values=True)


class Location(SchemaModel):
    lat: float
    lon: float


class PlanPreviewRequest(SchemaModel):
    user_id: str
    query: str = Field(min_length=1)
    city: str = "深圳"
    start_time: datetime
    duration_minutes: int = Field(gt=0, le=720)
    location: Location | None = None
    companion_ids: list[str] = Field(default_factory=list)


class ClarificationRequest(SchemaModel):
    session_id: str | None = None
    user_id: str | None = None
    query: str = Field(min_length=1)
    city: str | None = None
    start_time: datetime | None = None
    duration_minutes: int | None = Field(default=None, gt=0, le=720)
    location: Location | None = None


class ClarificationAnswer(SchemaModel):
    question_id: str
    answer: str = Field(min_length=1)


class ClarificationAnswerRequest(SchemaModel):
    answers: list[ClarificationAnswer] = Field(default_factory=list)


class PlanRevisionRequest(SchemaModel):
    message: str = Field(min_length=1)
    target_plan_id: str | None = None
    locked_items: list[dict[str, Any]] = Field(default_factory=list)
    revision_mode: Literal["partial", "full"] = "partial"


class PlanRevisionResponse(SchemaModel):
    plan: PlanOutput
    revision: PlanRevisionSummary


class HealthResponse(SchemaModel):
    status: str
    app: str
    env: str


class ExecutionResponse(SchemaModel):
    success: bool
    tasks: list[ExecutionTask]
    plan: PlanOutput


class FeedbackRequest(SchemaModel):
    rating: int | None = Field(default=None, ge=1, le=5)
    raw_feedback: str = Field(default="", max_length=2000)
    tags: list[str] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)


class FeedbackResponse(SchemaModel):
    success: bool
    session_id: str
    saved_feedback: dict[str, Any]


class PlaceFeedbackSubmitRequest(SchemaModel):
    poi_id: str
    rating: int | None = Field(default=None, ge=1, le=5)
    raw_feedback: str = Field(default="", max_length=1000)
    tags: list[str] = Field(default_factory=list)
    would_return: bool | None = None
    queue_minutes: int | None = Field(default=None, ge=0)
    crowd_level: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class FeedbackFollowupSubmitRequest(SchemaModel):
    rating: int | None = Field(default=None, ge=1, le=5)
    raw_feedback: str = Field(default="", max_length=2000)
    tags: list[str] = Field(default_factory=list)
    planning_reasonableness_rating: int | None = Field(default=None, ge=1, le=5)
    planning_feedback: str = Field(default="", max_length=1000)
    place_feedback: list[PlaceFeedbackSubmitRequest] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)


class FeedbackFollowupResponse(SchemaModel):
    task: FeedbackFollowupTask | None = None


class FeedbackFollowupSubmitResponse(SchemaModel):
    success: bool
    task: FeedbackFollowupTask
    saved_feedback: dict[str, Any]
    place_feedback: list[dict[str, Any]] = Field(default_factory=list)


class MetaSchemasResponse(SchemaModel):
    enums: dict[str, list[str]]
    render_hints: dict[str, Any]


class DataFileHealth(SchemaModel):
    logical_name: str
    exists: bool
    path: str
    record_count: int
    missing_required_fields: int
    warnings: list[str] = Field(default_factory=list)


class DataHealthResponse(SchemaModel):
    data_dir: str
    overall_status: str
    files: dict[str, DataFileHealth]
    warnings: list[str] = Field(default_factory=list)


PlanPreviewStreamEventType = Literal[
    # Legacy events (kept for backward compat)
    "step_start",
    "step_complete",
    "tool_call",
    "candidate_start",
    "candidate_complete",
    "plan_complete",
    "error",
    # New agent events
    "agent_action",
    "tool_observation",
    "state_updated",
    "plan_candidate_created",
    "constraint_violation_found",
    "plan_repaired",
    "score_updated",
    "clarification_required",
    "revision_started",
    "revision_intent_detected",
    "plan_patch_proposed",
    "plan_patch_applied",
    "plan_revalidated",
    "plan_rescored",
    "revision_complete",
]


class PlanPreviewStreamEvent(SchemaModel):
    event: PlanPreviewStreamEventType
    data: dict[str, Any] = Field(default_factory=dict)


def build_meta_schemas() -> MetaSchemasResponse:
    enum_classes = [
        RoleType,
        GroupType,
        ConflictType,
        StrategyType,
        StageType,
        PlanType,
        ExecutionAction,
        PlanState,
        EventType,
    ]
    return MetaSchemasResponse(
        enums={
            enum_class.__name__: [item.value for item in enum_class]
            for enum_class in enum_classes
        },
        render_hints={
            "timeline_item_types": ["activity", "transport", "dining", "buffer"],
            "plan_scores": ["overall_score", "min_role_score", "fairness_score"],
            "poi_card_fields": ["name", "category", "area", "avg_price", "queue_risk"],
        },
    )
