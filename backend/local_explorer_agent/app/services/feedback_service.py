from datetime import UTC, datetime
from uuid import uuid4

from local_explorer_agent.app.agent.plan_manager import SessionStore
from local_explorer_agent.app.domain.enums import PlanState
from local_explorer_agent.app.domain.schemas import FeedbackRequest, FeedbackResponse
from local_explorer_agent.app.services.memory_update_service import MemoryUpdateService


class FeedbackService:
    def __init__(
        self,
        *,
        session_store: SessionStore,
        memory_update_service: MemoryUpdateService | None = None,
    ) -> None:
        self.session_store = session_store
        self.memory_update_service = memory_update_service
        self._feedback: list[dict[str, object]] = []

    def submit_feedback(self, session_id: str, request: FeedbackRequest) -> FeedbackResponse:
        plan = self.session_store.get(session_id)
        record = {
            "feedback_id": f"fb_{uuid4().hex[:10]}",
            "session_id": session_id,
            "rating": request.rating,
            "raw_feedback": request.raw_feedback,
            "tags": request.tags,
            "payload": request.payload,
            "created_at": datetime.now(UTC).isoformat(),
        }
        self._feedback.append(record)
        if self.memory_update_service is not None:
            self.memory_update_service.apply_feedback(
                plan=plan,
                request=request,
                feedback_record=record,
            )
        plan.state = PlanState.FEEDBACK
        self.session_store.update(plan)
        return FeedbackResponse(success=True, session_id=session_id, saved_feedback=record)
