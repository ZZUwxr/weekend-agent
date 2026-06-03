from __future__ import annotations

from datetime import UTC, datetime

from local_explorer_agent.app.agent.plan_manager import SessionStore
from local_explorer_agent.app.domain.followup import FeedbackFollowupPlace, FeedbackFollowupTask
from local_explorer_agent.app.domain.place_feedback import PlaceFeedbackRecord
from local_explorer_agent.app.domain.schemas import (
    FeedbackFollowupSubmitRequest,
    FeedbackFollowupSubmitResponse,
    FeedbackRequest,
    PlaceFeedbackSubmitRequest,
)
from local_explorer_agent.app.repositories.feedback_followup_repository import (
    FeedbackFollowupRepository,
)
from local_explorer_agent.app.repositories.place_feedback_repository import (
    PlaceFeedbackRepository,
)
from local_explorer_agent.app.services.feedback_service import FeedbackService
from local_explorer_agent.app.tools.feedback_followup_tool import FeedbackFollowupTool


class FeedbackFollowupService:
    def __init__(
        self,
        *,
        session_store: SessionStore,
        repository: FeedbackFollowupRepository,
        place_feedback_repository: PlaceFeedbackRepository,
        feedback_service: FeedbackService,
        followup_tool: FeedbackFollowupTool | None = None,
    ) -> None:
        self.session_store = session_store
        self.repository = repository
        self.place_feedback_repository = place_feedback_repository
        self.feedback_service = feedback_service
        self.followup_tool = followup_tool or FeedbackFollowupTool()

    def schedule_for_plan(self, session_id: str) -> FeedbackFollowupTask:
        existing = self.repository.find_by_session(session_id)
        if existing is not None and existing.status != "cancelled":
            return existing

        plan = self.session_store.get(session_id)
        result = self.followup_tool.build_followup_task(plan=plan)
        if not result.success:
            raise ValueError(result.error_message or "Failed to build feedback followup")
        task = result.data
        if not isinstance(task, FeedbackFollowupTask):
            task = FeedbackFollowupTask.model_validate(task)
        return self.repository.save(task)

    def get_for_session(self, session_id: str) -> FeedbackFollowupTask | None:
        return self.repository.find_by_session(session_id)

    def list_due(
        self,
        *,
        user_id: str | None = None,
        now: datetime | None = None,
    ) -> list[FeedbackFollowupTask]:
        return self.repository.list_due(user_id=user_id, now=now)

    def submit_response(
        self,
        session_id: str,
        request: FeedbackFollowupSubmitRequest,
    ) -> FeedbackFollowupSubmitResponse:
        task = self.repository.find_by_session(session_id)
        if task is None:
            task = self.schedule_for_plan(session_id)

        place_by_id = {place.poi_id: place for place in task.places}
        place_records = [
            self._record_place_feedback(task, place_by_id, item)
            for item in request.place_feedback
        ]
        for record in place_records:
            self.place_feedback_repository.add_feedback(record)

        feedback_request = self._to_feedback_request(
            request,
            task=task,
            place_by_id=place_by_id,
        )
        feedback_response = self.feedback_service.submit_feedback(session_id, feedback_request)

        task.status = "completed"
        task.feedback_id = str(feedback_response.saved_feedback.get("feedback_id"))
        task.completed_at = datetime.now(UTC).isoformat()
        task = self.repository.save(task)
        return FeedbackFollowupSubmitResponse(
            success=True,
            task=task,
            saved_feedback=feedback_response.saved_feedback,
            place_feedback=[record.model_dump() for record in place_records],
        )

    def _record_place_feedback(
        self,
        task: FeedbackFollowupTask,
        place_by_id: dict[str, FeedbackFollowupPlace],
        item: PlaceFeedbackSubmitRequest,
    ) -> PlaceFeedbackRecord:
        place = place_by_id.get(item.poi_id)
        return PlaceFeedbackRecord(
            session_id=task.session_id,
            user_id=task.user_id,
            poi_id=item.poi_id,
            poi_name=place.name if place else None,
            category=place.category if place else None,
            rating=item.rating,
            tags=item.tags,
            raw_feedback=item.raw_feedback[:500],
            would_return=item.would_return,
            queue_minutes=item.queue_minutes,
            crowd_level=item.crowd_level,
            payload=item.payload,
        )

    def _to_feedback_request(
        self,
        request: FeedbackFollowupSubmitRequest,
        *,
        task: FeedbackFollowupTask,
        place_by_id: dict[str, FeedbackFollowupPlace],
    ) -> FeedbackRequest:
        place_lines = []
        liked_poi_ids: list[str] = []
        disliked_poi_ids: list[str] = []
        liked_categories: list[str] = []
        disliked_categories: list[str] = []
        ratings: list[int] = []

        for item in request.place_feedback:
            place = place_by_id.get(item.poi_id)
            label = place.name if place else item.poi_id
            if item.rating is not None:
                ratings.append(item.rating)
                if item.rating >= 4:
                    liked_poi_ids.append(item.poi_id)
                    if place:
                        liked_categories.append(place.category)
                elif item.rating <= 2:
                    disliked_poi_ids.append(item.poi_id)
                    if place:
                        disliked_categories.append(place.category)
            if item.raw_feedback:
                place_lines.append(f"{label}: {item.raw_feedback}")

        rating = request.rating or _average_rating(ratings)
        raw_feedback = _join_feedback_text(
            request.raw_feedback,
            request.planning_feedback,
            place_lines,
        )
        payload = {
            **request.payload,
            "feedback_source": "scheduled_followup",
            "followup_task_id": task.task_id,
            "planning_reasonableness_rating": request.planning_reasonableness_rating,
            "liked_poi_ids": _dedupe(liked_poi_ids),
            "disliked_poi_ids": _dedupe(disliked_poi_ids),
            "liked_categories": _dedupe(liked_categories),
            "disliked_categories": _dedupe(disliked_categories),
        }
        return FeedbackRequest(
            rating=rating,
            raw_feedback=raw_feedback[:2000],
            tags=_dedupe(["scheduled_followup", *request.tags]),
            payload=payload,
        )


def _average_rating(ratings: list[int]) -> int | None:
    if not ratings:
        return None
    return round(sum(ratings) / len(ratings))


def _join_feedback_text(
    overall: str,
    planning: str,
    place_lines: list[str],
) -> str:
    parts: list[str] = []
    if overall.strip():
        parts.append(f"整体体验：{overall.strip()}")
    if planning.strip():
        parts.append(f"行程合理性：{planning.strip()}")
    parts.extend(line for line in place_lines if line.strip())
    return "\n".join(parts)


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
