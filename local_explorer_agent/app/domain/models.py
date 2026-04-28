from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from local_explorer_agent.app.domain.enums import (
    ConflictType,
    DecisionType,
    EventType,
    ExecutionAction,
    ExecutionStatus,
    GroupType,
    PlanState,
    PlanType,
    RoleType,
    StageType,
    StrategyType,
    TimelineItemType,
)


class DomainModel(BaseModel):
    model_config = ConfigDict(use_enum_values=True)


class ExperienceScores(DomainModel):
    photo_score: float = Field(default=0.0, ge=0, le=5)
    conversation_score: float = Field(default=0.0, ge=0, le=5)
    novelty_score: float = Field(default=0.0, ge=0, le=5)
    relax_score: float = Field(default=0.0, ge=0, le=5)


class RoleProfile(DomainModel):
    role_id: str
    role_type: RoleType
    display_name: str
    age: int | None = Field(default=None, ge=0, le=120)
    hard_constraints: list[str] = Field(default_factory=list)
    soft_preferences: list[str] = Field(default_factory=list)
    hidden_needs: list[str] = Field(default_factory=list)
    risk_points: list[str] = Field(default_factory=list)
    priority_weight: float = Field(default=1.0, ge=0, le=5)
    confidence: float = Field(default=0.8, ge=0, le=1)


class GroupContext(DomainModel):
    group_type: GroupType = GroupType.UNKNOWN
    roles: list[RoleProfile] = Field(default_factory=list)
    group_size: int = Field(default=0, ge=0)
    scene_label: str = "unknown"
    inferred_constraints: list[str] = Field(default_factory=list)
    clarification_questions: list[str] = Field(default_factory=list)
    confidence_summary: dict[str, float] = Field(default_factory=dict)


class Conflict(DomainModel):
    conflict_id: str
    conflict_type: ConflictType
    involved_roles: list[str]
    description: str
    severity: int = Field(ge=1, le=5)
    affected_decisions: list[DecisionType]
    evidence: list[str] = Field(default_factory=list)
    resolution_hint: str


class NegotiationStrategy(DomainModel):
    strategy_id: str
    strategy_type: StrategyType
    target_conflicts: list[str] = Field(default_factory=list)
    explanation: str
    stage_policy: dict[str, Any] = Field(default_factory=dict)
    compensation_policy: dict[str, Any] = Field(default_factory=dict)


class POI(DomainModel):
    id: str
    name: str
    category: str
    city: str
    area: str | None = None
    address: str | None = None
    lon: float
    lat: float
    avg_price: int | None = None
    open_hours: str | None = None
    avg_stay_minutes: int | None = None
    indoor: bool = True
    weather_fit: list[str] = Field(default_factory=list)
    energy_level: int = Field(default=1, ge=0, le=5)
    crowd_risk: str = "medium"
    queue_risk: str = "medium"
    suitable_for: list[str] = Field(default_factory=list)
    activity_tags: list[str] = Field(default_factory=list)
    mood_tags: list[str] = Field(default_factory=list)
    experience_scores: ExperienceScores = Field(default_factory=ExperienceScores)
    facilities: dict[str, Any] = Field(default_factory=dict)
    business_rules: dict[str, Any] = Field(default_factory=dict)
    persona_fit: dict[str, float] = Field(default_factory=dict)
    conflict_relief_tags: list[str] = Field(default_factory=list)


class Stage(DomainModel):
    stage_id: str
    stage_type: StageType
    name: str
    experience_goal: str
    priority_role_id: str | None = None
    duration_minutes: int = Field(ge=0)
    energy_level: int = Field(default=1, ge=0, le=5)
    constraints: dict[str, Any] = Field(default_factory=dict)
    selected_poi: POI | None = None
    fallback_pois: list[POI] = Field(default_factory=list)
    reasoning: str = ""


class TimelineItem(DomainModel):
    time: str
    type: TimelineItemType
    poi_id: str | None = None
    poi_name: str | None = None
    mode: str | None = None
    duration_minutes: int = Field(ge=0)
    estimated_cost: float = Field(default=0, ge=0)
    notes: str = ""


class SatisfactionScore(DomainModel):
    role_id: str
    score: float = Field(ge=0, le=5)
    reasons: list[str] = Field(default_factory=list)
    sacrificed_points: list[str] = Field(default_factory=list)
    compensation: str | None = None


class PlanCandidate(DomainModel):
    plan_id: str
    plan_type: PlanType
    title: str
    theme: str
    strategy: NegotiationStrategy | None = None
    stages: list[Stage] = Field(default_factory=list)
    timeline: list[TimelineItem] = Field(default_factory=list)
    satisfaction_scores: list[SatisfactionScore] = Field(default_factory=list)
    overall_score: float = Field(default=0, ge=0, le=5)
    min_role_score: float = Field(default=0, ge=0, le=5)
    fairness_score: float = Field(default=0, ge=0, le=5)
    tradeoff_summary: str = ""
    recommendation_reason: str = ""
    route_segments: list[dict[str, Any]] = Field(default_factory=list)


class ExecutionTask(DomainModel):
    task_id: str
    action: ExecutionAction
    poi_id: str | None = None
    status: ExecutionStatus = ExecutionStatus.PENDING
    depends_on: list[str] = Field(default_factory=list)
    params: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] = Field(default_factory=dict)
    mock_scenario: str = "success"


class PlanOutput(DomainModel):
    session_id: str = Field(default_factory=lambda: f"sess_{uuid4().hex[:12]}")
    user_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    input_query: str
    inferred_context: GroupContext
    conflicts: list[Conflict] = Field(default_factory=list)
    negotiation_strategies: list[NegotiationStrategy] = Field(default_factory=list)
    plan_candidates: list[PlanCandidate] = Field(default_factory=list)
    recommended_plan_id: str
    execution_graph: list[ExecutionTask] = Field(default_factory=list)
    plan_version: int = 1
    state: PlanState = PlanState.PENDING
    share_message: str = ""
    replan_reason: str | None = None


class PlanEvent(DomainModel):
    event_id: str = Field(default_factory=lambda: f"evt_{uuid4().hex[:10]}")
    session_id: str
    event_type: EventType
    affected_poi_id: str | None = None
    affected_stage_id: str | None = None
    severity: int = Field(default=3, ge=1, le=5)
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
