from local_explorer_agent.app.core.exceptions import NotFoundError
from local_explorer_agent.app.domain.models import PlanOutput


class SessionStore:
    def __init__(self) -> None:
        self._plans: dict[str, PlanOutput] = {}

    def save(self, plan: PlanOutput) -> PlanOutput:
        self._plans[plan.session_id] = plan
        return plan

    def get(self, session_id: str) -> PlanOutput:
        try:
            return self._plans[session_id]
        except KeyError as exc:
            raise NotFoundError(f"Plan session {session_id} not found") from exc

    def update(self, plan: PlanOutput) -> PlanOutput:
        self._plans[plan.session_id] = plan
        return plan
