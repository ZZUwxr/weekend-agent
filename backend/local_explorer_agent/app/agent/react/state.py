from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from local_explorer_agent.app.agent.react.actions import AgentAction, AgentActionType
from local_explorer_agent.app.domain.memory import UserMemoryContext
from local_explorer_agent.app.domain.models import (
    ClarificationResponse,
    Conflict,
    ExecutionTask,
    GroupContext,
    NegotiationStrategy,
    PlanCandidate,
    PlanEvent,
    PlanOutput,
    PlanPatch,
    PlanRevisionSummary,
    RequirementIntake,
)
from local_explorer_agent.app.domain.schemas import PlanPreviewRequest
from local_explorer_agent.app.domain.validation import PlanValidationResult


class AgentObservation(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    action_type: AgentActionType
    tool_name: str | None = None
    success: bool
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    warnings: list[str] = Field(default_factory=list)
    confidence: float | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AgentTraceStep(BaseModel):
    step_index: int
    action: AgentAction
    observation: AgentObservation | None = None
    state_summary: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AgentState(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    session_id: str
    user_id: str
    request: PlanPreviewRequest

    status: Literal[
        "running",
        "needs_user_input",
        "ready_to_finalize",
        "completed",
        "failed",
    ] = "running"

    goal: str | None = None
    user_memory: UserMemoryContext | None = None
    requirement_intake: RequirementIntake | None = None

    inferred_context: GroupContext | None = None

    known_constraints: list[str] = Field(default_factory=list)
    missing_slots: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    clarification_response: ClarificationResponse | None = None
    clarification_answers: dict[str, str] = Field(default_factory=dict)

    conflicts: list[Conflict] = Field(default_factory=list)
    negotiation_strategies: list[NegotiationStrategy] = Field(default_factory=list)

    candidate_plans: list[PlanCandidate] = Field(default_factory=list)
    recommended_plan_id: str | None = None

    validation_result: PlanValidationResult | None = None
    scoring_completed: bool = False
    repair_count: int = 0
    warnings: list[str] = Field(default_factory=list)

    execution_graph: list[ExecutionTask] = Field(default_factory=list)

    observations: list[AgentObservation] = Field(default_factory=list)
    trace: list[AgentTraceStep] = Field(default_factory=list)

    step_count: int = 0
    tool_call_count: int = 0

    # Interactive planning support
    is_revision: bool = False
    revision_instruction: str | None = None
    revision_target_plan_id: str | None = None
    revision_mode: Literal["partial", "full"] = "partial"
    revision_intents: list[str] = Field(default_factory=list)
    locked_items: list[dict[str, Any]] = Field(default_factory=list)
    revision_patches: list[PlanPatch] = Field(default_factory=list)
    revision_summary: PlanRevisionSummary | None = None
    revision_count: int = 0

    # Replan support
    is_replan: bool = False
    original_plan: PlanOutput | None = None
    trigger_event: PlanEvent | None = None

    def to_llm_summary(self, *, max_observations: int = 5) -> dict[str, Any]:
        req = self.request
        ctx = self.inferred_context
        memory_summary = (
            self.user_memory.compact_summary() if self.user_memory is not None else None
        )
        intake_summary = _requirement_intake_summary(self.requirement_intake)

        roles_summary: list[dict[str, Any]] = []
        if ctx:
            roles_summary = [
                {
                    "role_type": r.role_type,
                    "display_name": r.display_name,
                    "hard_constraints_count": len(r.hard_constraints),
                    "soft_preferences_count": len(r.soft_preferences),
                    "risk_points_count": len(r.risk_points),
                }
                for r in ctx.roles
            ]

        conflicts_summary: list[dict[str, Any]] = [
            {"type": c.conflict_type, "description": _clip_text(c.description)}
            for c in self.conflicts[:5]
        ]

        candidates_summary: list[dict[str, Any]] = []
        for p in self.candidate_plans:
            has_poi = all(s.selected_poi is not None for s in p.stages) if p.stages else False
            selected_poi_count = sum(1 for stage in p.stages if stage.selected_poi is not None)
            candidates_summary.append({
                "plan_id": p.plan_id,
                "title": p.title,
                "stage_count": len(p.stages),
                "has_poi": has_poi,
                "has_route": bool(p.route_segments) or selected_poi_count <= 1,
                "has_timeline": bool(p.timeline),
                "overall_score": p.overall_score,
                "min_role_score": p.min_role_score,
                "fairness_score": p.fairness_score,
            })

        vr = self.validation_result
        vr_summary = None
        if vr is not None:
            top_violations = [
                _clip_text(v.message)
                for v in [*vr.blocking_violations, *vr.warnings][:3]
            ]
            vr_summary = {
                "passed": vr.passed,
                "blocking_count": len(vr.blocking_violations),
                "warning_count": len(vr.warnings),
                "top_violation_messages": top_violations,
            }

        recent: list[dict[str, Any]] = []
        for obs in self.observations[-max_observations:]:
            summary: dict[str, Any] = {
                "action_type": obs.action_type,
                "tool_name": obs.tool_name,
                "success": obs.success,
            }
            if obs.data:
                summary["data_keys"] = list(obs.data.keys())[:5]
            if obs.error:
                summary["error"] = _clip_text(obs.error)
            recent.append(summary)

        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "query": _clip_text(req.query, 500),
            "city": req.city,
            "start_time": req.start_time.isoformat(),
            "duration_minutes": req.duration_minutes,
            "has_location": req.location is not None,
            "status": self.status,
            "user_memory": memory_summary,
            "requirement_intake": intake_summary,
            "inferred_context_done": ctx is not None,
            "group_type": ctx.group_type if ctx else None,
            "inferred_context_summary": {
                "scene_label": ctx.scene_label if ctx else None,
                "group_size": ctx.group_size if ctx else 0,
                "constraints_count": len(ctx.inferred_constraints) if ctx else 0,
                "clarification_questions_count": (
                    len(ctx.clarification_questions) if ctx else 0
                ),
            },
            "roles_summary": roles_summary,
            "conflicts_count": len(self.conflicts),
            "conflicts_summary": conflicts_summary,
            "strategies_count": len(self.negotiation_strategies),
            "candidates_summary": candidates_summary,
            "recommended_plan_id": self.recommended_plan_id,
            "validation_result_summary": vr_summary,
            "scoring_completed": self.scoring_completed,
            "step_count": self.step_count,
            "tool_call_count": self.tool_call_count,
            "repair_count": self.repair_count,
            "missing_slots": self.missing_slots,
            "assumptions": self.assumptions,
            "clarification": _clarification_summary(self.clarification_response),
            "clarification_answers_count": len(self.clarification_answers),
            "known_constraints": self.known_constraints[:10],
            "recent_observations": recent,
            "is_replan": self.is_replan,
            "trigger_event_summary": _event_summary(self.trigger_event),
            "is_revision": self.is_revision,
            "revision_instruction": _clip_text(self.revision_instruction, 300),
            "revision_target_plan_id": self.revision_target_plan_id,
            "revision_mode": self.revision_mode,
            "revision_intents": self.revision_intents,
            "locked_items_count": len(self.locked_items),
            "revision_patches_count": len(self.revision_patches),
        }


def _clip_text(value: str | None, limit: int = 160) -> str:
    if not value:
        return ""
    text = str(value)
    return text if len(text) <= limit else f"{text[:limit]}..."


def _event_summary(event: PlanEvent | None) -> dict[str, Any] | None:
    if event is None:
        return None
    return {
        "event_type": event.event_type,
        "affected_poi_id": event.affected_poi_id,
        "affected_stage_id": event.affected_stage_id,
        "severity": event.severity,
        "payload_keys": list(event.payload.keys())[:5],
    }


def _clarification_summary(
    clarification: ClarificationResponse | None,
) -> dict[str, Any] | None:
    if clarification is None:
        return None
    return {
        "needs_clarification": clarification.needs_clarification,
        "question_count": len(clarification.questions),
        "required_count": sum(1 for q in clarification.questions if q.required),
        "can_continue_with_assumptions": clarification.can_continue_with_assumptions,
        "safe_assumptions": clarification.safe_assumptions[:5],
    }


def _requirement_intake_summary(
    intake: RequirementIntake | None,
) -> dict[str, Any] | None:
    if intake is None:
        return None
    return {
        "primary_intent": intake.primary_intent,
        "intent_scope": intake.intent_scope,
        "activity_count": intake.activity_count.model_dump(),
        "known_constraints": intake.known_constraints[:8],
        "missing_slots": intake.missing_slots[:8],
        "required_slots": {
            key: value
            for key, value in intake.required_slots.items()
            if value not in (None, "", [])
        },
        "clarification": _clarification_summary(intake.clarification),
        "search_hints": intake.search_hints,
    }
