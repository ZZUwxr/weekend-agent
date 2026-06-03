from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from local_explorer_agent.app.domain.memory import UserMemory, UserMemoryFeedback
from local_explorer_agent.app.domain.models import POI, PlanCandidate, PlanOutput
from local_explorer_agent.app.domain.schemas import FeedbackRequest
from local_explorer_agent.app.repositories.user_memory_repository import UserMemoryRepository

_WEIGHT_MIN = 0.5
_WEIGHT_MAX = 1.8
_POSITIVE_DELTA = 0.1
_NEGATIVE_DELTA = -0.15

_CATEGORY_KEYWORDS = {
    "咖啡": "咖啡",
    "书店": "书店",
    "展览": "展览",
    "看展": "展览",
    "火锅": "火锅",
    "烧烤": "烧烤",
    "烤肉": "烤肉",
    "轻食": "轻食",
    "甜品": "甜品",
    "公园": "公园",
    "桌游": "桌游",
    "密室": "密室逃脱",
}
_TAG_KEYWORDS = {
    "安静": "安静",
    "松弛": "松弛",
    "轻松": "松弛",
    "低步行": "低步行",
    "走路少": "低步行",
    "不排队": "少排队",
    "排队": "排队",
    "太吵": "热闹",
    "热闹": "热闹",
    "互动": "互动",
    "新鲜": "新鲜感",
    "孩子": "亲子",
}


class MemoryUpdateService:
    def __init__(self, repository: UserMemoryRepository) -> None:
        self.repository = repository

    def apply_feedback(
        self,
        *,
        plan: PlanOutput,
        request: FeedbackRequest,
        feedback_record: dict[str, Any],
    ) -> None:
        memory = self.repository.get_or_create(plan.user_id)
        self._append_feedback(memory, feedback_record)

        delta = self._rating_delta(request.rating)
        if delta == 0:
            memory.updated_at = _now_iso()
            self.repository.save(memory)
            return

        candidate = _recommended_candidate(plan)
        selected_pois = _selected_pois(candidate)
        payload = request.payload or {}

        liked_categories = _list_strings(payload.get("liked_categories"))
        disliked_categories = _list_strings(payload.get("disliked_categories"))
        liked_poi_ids = _list_strings(payload.get("liked_poi_ids"))
        disliked_poi_ids = _list_strings(payload.get("disliked_poi_ids"))

        raw_categories, raw_tags = _extract_feedback_terms(request.raw_feedback)
        poi_categories = [poi.category for poi in selected_pois]
        poi_tags = _poi_tags(selected_pois)
        poi_ids = [poi.id for poi in selected_pois]

        if delta > 0:
            categories = liked_categories or [*poi_categories, *raw_categories]
            tags = [*poi_tags, *raw_tags]
            self._bump_weights(memory.preferences.category_weights, categories, delta)
            self._bump_weights(memory.preferences.tag_weights, tags, delta)
            memory.preferences.liked_poi_ids = _dedupe([
                *memory.preferences.liked_poi_ids,
                *(liked_poi_ids or poi_ids),
            ])
        else:
            categories = disliked_categories or [*poi_categories, *raw_categories]
            tags = [*poi_tags, *raw_tags]
            self._bump_weights(memory.preferences.category_weights, categories, delta)
            self._bump_weights(memory.preferences.tag_weights, tags, delta)
            memory.preferences.disliked_poi_ids = _dedupe([
                *memory.preferences.disliked_poi_ids,
                *(disliked_poi_ids or poi_ids),
            ])

        memory.updated_at = _now_iso()
        self.repository.save(memory)

    def _append_feedback(
        self,
        memory: UserMemory,
        feedback_record: dict[str, Any],
    ) -> None:
        memory.feedback_history.append(
            UserMemoryFeedback(
                feedback_id=str(feedback_record["feedback_id"]),
                session_id=str(feedback_record["session_id"]),
                rating=feedback_record.get("rating"),
                tags=[str(tag) for tag in feedback_record.get("tags", [])],
                raw_feedback=str(feedback_record.get("raw_feedback", ""))[:500],
                created_at=str(feedback_record["created_at"]),
            )
        )
        memory.feedback_history = memory.feedback_history[-50:]

    def _bump_weights(
        self,
        weights: dict[str, float],
        terms: list[str],
        delta: float,
    ) -> None:
        for term in _dedupe(terms):
            if not term:
                continue
            weights[term] = _clamp_weight(float(weights.get(term, 1.0)) + delta)

    def _rating_delta(self, rating: int | None) -> float:
        if rating is None:
            return 0.0
        if rating >= 4:
            return _POSITIVE_DELTA
        if rating <= 2:
            return _NEGATIVE_DELTA
        return 0.0


def _recommended_candidate(plan: PlanOutput) -> PlanCandidate | None:
    return next(
        (
            candidate
            for candidate in plan.plan_candidates
            if candidate.plan_id == plan.recommended_plan_id
        ),
        plan.plan_candidates[0] if plan.plan_candidates else None,
    )


def _selected_pois(candidate: PlanCandidate | None) -> list[POI]:
    if candidate is None:
        return []
    return [stage.selected_poi for stage in candidate.stages if stage.selected_poi is not None]


def _poi_tags(pois: list[POI]) -> list[str]:
    tags: list[str] = []
    for poi in pois:
        tags.extend(poi.activity_tags)
        tags.extend(poi.mood_tags)
        tags.extend(poi.suitable_for)
        tags.extend(poi.conflict_relief_tags)
    return tags


def _extract_feedback_terms(raw_feedback: str) -> tuple[list[str], list[str]]:
    categories: list[str] = []
    tags: list[str] = []
    for keyword, category in _CATEGORY_KEYWORDS.items():
        if keyword in raw_feedback:
            categories.append(category)
    for keyword, tag in _TAG_KEYWORDS.items():
        if keyword in raw_feedback:
            tags.append(tag)
    return _dedupe(categories), _dedupe(tags)


def _list_strings(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    return []


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _clamp_weight(value: float) -> float:
    return round(min(_WEIGHT_MAX, max(_WEIGHT_MIN, value)), 2)


def _now_iso() -> str:
    return datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()
