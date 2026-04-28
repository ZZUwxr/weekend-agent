from datetime import datetime
from typing import Any

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
from local_explorer_agent.app.domain.models import ExecutionTask, PlanOutput


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
