from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import TYPE_CHECKING

from local_explorer_agent.app.agent.orchestrator import Orchestrator
from local_explorer_agent.app.agent.plan_manager import SessionStore
from local_explorer_agent.app.domain.enums import PlanState
from local_explorer_agent.app.domain.models import PlanEvent, PlanOutput, PlanRevisionSummary
from local_explorer_agent.app.domain.schemas import (
    ClarificationAnswerRequest,
    PlanPreviewRequest,
    PlanPreviewStreamEvent,
    PlanRevisionRequest,
    PlanRevisionResponse,
)

if TYPE_CHECKING:
    from local_explorer_agent.app.agent.react.runtime import ReActAgentRuntime
    from local_explorer_agent.app.services.feedback_followup_service import (
        FeedbackFollowupService,
    )


class PlanService:
    def __init__(
        self,
        *,
        orchestrator: Orchestrator | None = None,
        session_store: SessionStore,
        react_runtime: ReActAgentRuntime | None = None,
        feedback_followup_service: FeedbackFollowupService | None = None,
    ) -> None:
        self.orchestrator = orchestrator
        self.session_store = session_store
        self.react_runtime = react_runtime
        self.feedback_followup_service = feedback_followup_service

    def preview_plan(
        self,
        request: PlanPreviewRequest,
        event_callback: Callable[[PlanPreviewStreamEvent], None] | None = None,
    ) -> PlanOutput:
        if self.react_runtime is not None:
            from local_explorer_agent.app.agent.react.events import AgentEventEmitter

            emitter = AgentEventEmitter(event_callback) if event_callback else None
            plan = asyncio.run(self.react_runtime.run(request, event_emitter=emitter))
            if self.react_runtime.last_state is not None:
                self.session_store.save_agent_state(
                    plan.session_id,
                    self.react_runtime.last_state,
                )
            return self.session_store.save(plan)

        assert self.orchestrator is not None
        return self.orchestrator.preview_plan(request, event_callback=event_callback)

    def get_plan(self, session_id: str) -> PlanOutput:
        return self.session_store.get(session_id)

    def confirm_plan(self, session_id: str) -> PlanOutput:
        plan = self.session_store.get(session_id)
        if plan.state in {
            PlanState.CONFIRMED,
            PlanState.EXECUTING,
            PlanState.COMPLETED,
            PlanState.FAILED,
            PlanState.FEEDBACK,
        }:
            return plan
        plan.state = PlanState.CONFIRMED
        saved = self.session_store.update(plan)
        if self.feedback_followup_service is not None:
            self.feedback_followup_service.schedule_for_plan(session_id)
        return saved

    def answer_clarifications(
        self,
        session_id: str,
        request: ClarificationAnswerRequest,
        event_callback: Callable[[PlanPreviewStreamEvent], None] | None = None,
    ) -> PlanOutput:
        if self.react_runtime is None:
            raise ValueError("Clarification loop is only available in react runtime")

        plan = self.session_store.get(session_id)
        if plan.state != PlanState.CLARIFYING:
            raise ValueError("Plan is not waiting for clarification")

        state = self.session_store.get_agent_state(session_id)
        answers = {answer.question_id: answer.answer for answer in request.answers}
        answer_notes = [f"{qid}: {answer}" for qid, answer in answers.items()]
        query_suffix = "；".join(answer_notes)
        updated_request = state.request.model_copy(
            update={"query": f"{state.request.query}\n用户澄清：{query_suffix}"}
        )
        state = state.model_copy(
            update={
                "request": updated_request,
                "requirement_intake": None,
                "clarification_response": None,
                "missing_slots": [],
                "clarification_answers": {**state.clarification_answers, **answers},
                "assumptions": [*state.assumptions, *answer_notes],
                "status": "running",
            }
        )

        from local_explorer_agent.app.agent.react.events import AgentEventEmitter

        emitter = AgentEventEmitter(event_callback) if event_callback else None
        updated_plan = asyncio.run(
            self.react_runtime.run_from_state(state, event_emitter=emitter)
        )
        if self.react_runtime.last_state is not None:
            self.session_store.save_agent_state(
                updated_plan.session_id,
                self.react_runtime.last_state,
            )
        return self.session_store.update(updated_plan)

    def revise_plan(
        self,
        session_id: str,
        request: PlanRevisionRequest,
        event_callback: Callable[[PlanPreviewStreamEvent], None] | None = None,
    ) -> PlanRevisionResponse:
        if self.react_runtime is None:
            raise ValueError("Plan revision is only available in react runtime")

        plan = self.session_store.get(session_id)
        if plan.state not in {PlanState.PREVIEW, PlanState.REVISING}:
            raise ValueError(
                "Only preview or revising plans can be revised; "
                "confirmed/executing/completed plans require a new plan"
            )

        from local_explorer_agent.app.agent.react.events import AgentEventEmitter

        emitter = AgentEventEmitter(event_callback) if event_callback else None
        revised = asyncio.run(
            self.react_runtime.run_revision(plan, request, event_emitter=emitter)
        )
        if self.react_runtime.last_state is not None:
            self.session_store.save_agent_state(
                revised.session_id,
                self.react_runtime.last_state,
            )
        saved = self.session_store.update(revised)
        revision = saved.revision_summary or PlanRevisionSummary(
            summary="已根据用户意见检查方案，未产生结构化修改。"
        )
        return PlanRevisionResponse(plan=saved, revision=revision)

    def handle_event(self, session_id: str, event: PlanEvent) -> PlanOutput:
        plan = self.session_store.get(session_id)

        if self.react_runtime is not None:
            replan_plan = asyncio.run(self.react_runtime.run_replan(plan, event))
            if self.react_runtime.last_state is not None:
                self.session_store.save_agent_state(
                    replan_plan.session_id,
                    self.react_runtime.last_state,
                )
            return self.session_store.update(replan_plan)

        assert self.orchestrator is not None
        return self.orchestrator.replan(session_id=session_id, event=event)
