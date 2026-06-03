from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MemoryModel(BaseModel):
    model_config = ConfigDict(use_enum_values=True)


class UserMemoryProfile(MemoryModel):
    home_area: str | None = None
    default_city: str = "深圳"
    default_duration_minutes: int = Field(default=240, ge=30, le=720)
    budget_preference: str = "medium"
    pace_preference: str = "relaxed"
    max_walking_minutes_per_segment: int | None = Field(default=15, ge=0, le=120)


class UserMemoryCompanion(MemoryModel):
    companion_id: str
    display_name: str
    role_type: str
    age: int | None = Field(default=None, ge=0, le=120)
    hard_constraints: list[str] = Field(default_factory=list)
    soft_preferences: list[str] = Field(default_factory=list)
    risk_points: list[str] = Field(default_factory=list)


class UserMemoryPreferences(MemoryModel):
    likes: list[str] = Field(default_factory=list)
    dislikes: list[str] = Field(default_factory=list)
    category_weights: dict[str, float] = Field(default_factory=dict)
    tag_weights: dict[str, float] = Field(default_factory=dict)
    liked_poi_ids: list[str] = Field(default_factory=list)
    disliked_poi_ids: list[str] = Field(default_factory=list)

    @field_validator("category_weights", "tag_weights")
    @classmethod
    def clamp_weights(cls, value: dict[str, float]) -> dict[str, float]:
        return {
            str(key): _clamp_weight(raw_value)
            for key, raw_value in value.items()
            if key
        }


class UserMemoryFeedback(MemoryModel):
    feedback_id: str
    session_id: str
    rating: int | None = Field(default=None, ge=1, le=5)
    tags: list[str] = Field(default_factory=list)
    raw_feedback: str = Field(default="", max_length=500)
    created_at: str


class UserMemory(MemoryModel):
    schema_version: int = 1
    user_id: str
    display_name: str | None = None
    updated_at: str
    profile: UserMemoryProfile = Field(default_factory=UserMemoryProfile)
    companions: list[UserMemoryCompanion] = Field(default_factory=list)
    preferences: UserMemoryPreferences = Field(default_factory=UserMemoryPreferences)
    feedback_history: list[UserMemoryFeedback] = Field(default_factory=list)


class UserMemoryContext(MemoryModel):
    user_id: str
    profile: UserMemoryProfile = Field(default_factory=UserMemoryProfile)
    companions: list[UserMemoryCompanion] = Field(default_factory=list)
    selected_companion_ids: list[str] = Field(default_factory=list)
    likes: list[str] = Field(default_factory=list)
    dislikes: list[str] = Field(default_factory=list)
    category_weights: dict[str, float] = Field(default_factory=dict)
    tag_weights: dict[str, float] = Field(default_factory=dict)
    liked_poi_ids: list[str] = Field(default_factory=list)
    disliked_poi_ids: list[str] = Field(default_factory=list)

    def compact_summary(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "budget_preference": self.profile.budget_preference,
            "pace_preference": self.profile.pace_preference,
            "max_walking_minutes_per_segment": self.profile.max_walking_minutes_per_segment,
            "likes": self.likes[:8],
            "dislikes": self.dislikes[:8],
            "top_category_weights": _top_weights(self.category_weights),
            "top_tag_weights": _top_weights(self.tag_weights),
            "companions": [
                {
                    "companion_id": companion.companion_id,
                    "display_name": companion.display_name,
                    "role_type": companion.role_type,
                    "hard_constraints_count": len(companion.hard_constraints),
                    "soft_preferences_count": len(companion.soft_preferences),
                }
                for companion in self.companions[:5]
            ],
            "selected_companion_ids": self.selected_companion_ids[:8],
            "liked_poi_ids": self.liked_poi_ids[:8],
            "disliked_poi_ids": self.disliked_poi_ids[:8],
        }


def memory_to_context(memory: UserMemory) -> UserMemoryContext:
    preferences = memory.preferences
    return UserMemoryContext(
        user_id=memory.user_id,
        profile=memory.profile,
        companions=memory.companions,
        selected_companion_ids=[],
        likes=preferences.likes,
        dislikes=preferences.dislikes,
        category_weights=preferences.category_weights,
        tag_weights=preferences.tag_weights,
        liked_poi_ids=preferences.liked_poi_ids,
        disliked_poi_ids=preferences.disliked_poi_ids,
    )


def new_default_memory(user_id: str, *, now: datetime) -> UserMemory:
    return UserMemory(
        user_id=user_id,
        display_name=None,
        updated_at=now.isoformat(),
        profile=UserMemoryProfile(),
        companions=[
            UserMemoryCompanion(
                companion_id="comp_spouse",
                display_name="老婆",
                role_type="spouse",
                hard_constraints=["减脂期，餐饮优先低卡或可控热量"],
                soft_preferences=["安静舒适", "轻松不赶"],
                risk_points=["高热量聚餐", "排队太久"],
            ),
            UserMemoryCompanion(
                companion_id="comp_child",
                display_name="儿子",
                role_type="child",
                age=5,
                hard_constraints=["需要适合5岁儿童", "避免过长步行"],
                soft_preferences=["互动体验", "寓教于乐"],
                risk_points=["等待太久", "过于嘈杂"],
            ),
        ],
        preferences=UserMemoryPreferences(
            likes=[],
            dislikes=[],
            category_weights={},
            tag_weights={},
            liked_poi_ids=[],
            disliked_poi_ids=[],
        ),
        feedback_history=[],
    )


def _clamp_weight(value: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 1.0
    return round(min(1.8, max(0.5, number)), 2)


def _top_weights(weights: dict[str, float]) -> dict[str, float]:
    ranked = sorted(weights.items(), key=lambda item: abs(item[1] - 1.0), reverse=True)
    return dict(ranked[:8])
