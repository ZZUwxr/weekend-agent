from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta

from local_explorer_agent.app.domain.followup import (
    FeedbackFollowupPlace,
    FeedbackFollowupQuestion,
    FeedbackFollowupTask,
)
from local_explorer_agent.app.domain.models import PlanCandidate, PlanOutput
from local_explorer_agent.app.tools.base import BaseTool, ToolResult


class FeedbackFollowupTool(BaseTool):
    name = "feedback_followup_tool"

    def build_followup_task(
        self,
        *,
        plan: PlanOutput,
        due_at: datetime | None = None,
    ) -> ToolResult:
        started_at = time.perf_counter()
        candidate = _recommended_candidate(plan)
        places = _followup_places(candidate)
        due = due_at or _default_due_at(plan)
        questions = [
            FeedbackFollowupQuestion(
                question_id="overall_experience",
                question="这次整体玩下来体验怎么样？有哪些满意或不满意的地方？",
                target="overall",
            ),
            FeedbackFollowupQuestion(
                question_id="planning_reasonableness",
                question="这次行程规划是否合理？节奏、转场、时间安排有没有问题？",
                target="planning",
            ),
            *[
                FeedbackFollowupQuestion(
                    question_id=f"place_{place.poi_id}",
                    question=(
                        f"{place.name} 实际体验如何？可以说说排队、环境、服务、"
                        "出品/活动质量，以及下次还会不会去。"
                    ),
                    target="place",
                    poi_id=place.poi_id,
                )
                for place in places
            ],
        ]
        task = FeedbackFollowupTask(
            session_id=plan.session_id,
            user_id=plan.user_id,
            plan_id=candidate.plan_id if candidate else plan.recommended_plan_id,
            due_at=due.isoformat(),
            questions=questions,
            places=places,
        )
        return self._result(data=task, started_at=started_at)


def _recommended_candidate(plan: PlanOutput) -> PlanCandidate | None:
    return next(
        (
            candidate
            for candidate in plan.plan_candidates
            if candidate.plan_id == plan.recommended_plan_id
        ),
        plan.plan_candidates[0] if plan.plan_candidates else None,
    )


def _followup_places(candidate: PlanCandidate | None) -> list[FeedbackFollowupPlace]:
    if candidate is None:
        return []
    places: list[FeedbackFollowupPlace] = []
    seen: set[str] = set()
    for stage in candidate.stages:
        poi = stage.selected_poi
        if poi is None or poi.id in seen:
            continue
        seen.add(poi.id)
        places.append(
            FeedbackFollowupPlace(
                stage_id=stage.stage_id,
                stage_name=stage.name,
                poi_id=poi.id,
                name=poi.name,
                category=poi.category,
                area=poi.area,
            )
        )
    return places


def _default_due_at(plan: PlanOutput) -> datetime:
    if plan.created_at.tzinfo is None:
        created_at = plan.created_at.replace(tzinfo=UTC)
    else:
        created_at = plan.created_at
    return created_at + timedelta(hours=6)
