from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class PlaceFeedbackModel(BaseModel):
    model_config = ConfigDict(use_enum_values=True)


class PlaceFeedbackRecord(PlaceFeedbackModel):
    feedback_id: str = Field(default_factory=lambda: f"pfb_{uuid4().hex[:10]}")
    session_id: str
    user_id: str
    poi_id: str
    poi_name: str | None = None
    category: str | None = None
    rating: int | None = Field(default=None, ge=1, le=5)
    tags: list[str] = Field(default_factory=list)
    raw_feedback: str = Field(default="", max_length=500)
    would_return: bool | None = None
    queue_minutes: int | None = Field(default=None, ge=0)
    crowd_level: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class PlaceFeedbackSummary(PlaceFeedbackModel):
    poi_id: str
    feedback_count: int = 0
    avg_rating: float | None = None
    positive_count: int = 0
    negative_count: int = 0
    tag_counts: dict[str, int] = Field(default_factory=dict)
    recent_notes: list[str] = Field(default_factory=list)
    updated_at: str | None = None


class PlaceFeedbackFile(PlaceFeedbackModel):
    schema_version: int = 1
    poi_id: str
    records: list[PlaceFeedbackRecord] = Field(default_factory=list)


def summarize_place_feedback(
    poi_id: str,
    records: list[PlaceFeedbackRecord],
) -> PlaceFeedbackSummary:
    rated = [record.rating for record in records if record.rating is not None]
    tag_counter: Counter[str] = Counter()
    for record in records:
        tag_counter.update(tag for tag in record.tags if tag)

    recent_notes = [
        record.raw_feedback.strip()
        for record in records[-5:]
        if record.raw_feedback.strip()
    ]
    updated_at = records[-1].created_at if records else None

    return PlaceFeedbackSummary(
        poi_id=poi_id,
        feedback_count=len(records),
        avg_rating=round(sum(rated) / len(rated), 2) if rated else None,
        positive_count=sum(1 for rating in rated if rating >= 4),
        negative_count=sum(1 for rating in rated if rating <= 2),
        tag_counts=dict(tag_counter.most_common(20)),
        recent_notes=recent_notes,
        updated_at=updated_at,
    )
