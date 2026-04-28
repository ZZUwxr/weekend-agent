from local_explorer_agent.app.agent.orchestrator import Orchestrator
from local_explorer_agent.app.agent.plan_manager import SessionStore
from local_explorer_agent.app.domain.enums import PlanState
from local_explorer_agent.app.domain.models import PlanEvent, PlanOutput
from local_explorer_agent.app.domain.schemas import PlanPreviewRequest


class PlanService:
    def __init__(self, *, orchestrator: Orchestrator, session_store: SessionStore) -> None:
        self.orchestrator = orchestrator
        self.session_store = session_store

    def preview_plan(self, request: PlanPreviewRequest) -> PlanOutput:
        return self.orchestrator.preview_plan(request)

    def get_plan(self, session_id: str) -> PlanOutput:
        return self.session_store.get(session_id)

    def confirm_plan(self, session_id: str) -> PlanOutput:
        plan = self.session_store.get(session_id)
        plan.state = PlanState.CONFIRMED
        return self.session_store.update(plan)

    def handle_event(self, session_id: str, event: PlanEvent) -> PlanOutput:
        return self.orchestrator.replan(session_id=session_id, event=event)
