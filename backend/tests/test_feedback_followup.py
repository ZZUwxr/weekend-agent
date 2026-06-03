from __future__ import annotations

import json

import pytest

from local_explorer_agent.app.agent.plan_manager import SessionStore
from local_explorer_agent.app.domain.enums import PlanState, PlanType, StageType
from local_explorer_agent.app.domain.models import (
    POI,
    GroupContext,
    PlanCandidate,
    PlanOutput,
    Stage,
)
from local_explorer_agent.app.domain.place_feedback import PlaceFeedbackRecord
from local_explorer_agent.app.domain.schemas import (
    FeedbackFollowupSubmitRequest,
    PlaceFeedbackSubmitRequest,
)
from local_explorer_agent.app.repositories.feedback_followup_repository import (
    FeedbackFollowupRepository,
)
from local_explorer_agent.app.repositories.place_feedback_repository import (
    PlaceFeedbackRepository,
)
from local_explorer_agent.app.repositories.poi_repository import POIRepository
from local_explorer_agent.app.repositories.user_memory_repository import UserMemoryRepository
from local_explorer_agent.app.services.feedback_followup_service import (
    FeedbackFollowupService,
)
from local_explorer_agent.app.services.feedback_service import FeedbackService
from local_explorer_agent.app.services.memory_update_service import MemoryUpdateService
from local_explorer_agent.app.services.plan_service import PlanService


def _poi(poi_id: str, category: str, name: str | None = None) -> POI:
    return POI(
        id=poi_id,
        name=name or poi_id,
        category=category,
        city="深圳",
        lon=114.0,
        lat=22.5,
        queue_risk="low",
        mood_tags=["安静"],
        activity_tags=["聊天"],
    )


def _candidate(*pois: POI) -> PlanCandidate:
    return PlanCandidate(
        plan_id="plan_a",
        plan_type=PlanType.PLAN_A,
        title="测试方案",
        theme="test",
        stages=[
            Stage(
                stage_id=f"stage_{poi.id}",
                stage_type=StageType.EXPLORE,
                name=poi.name,
                experience_goal="体验",
                duration_minutes=60,
                selected_poi=poi,
                constraints={"categories": [poi.category]},
            )
            for poi in pois
        ],
    )


def _plan(*pois: POI) -> PlanOutput:
    return PlanOutput(
        user_id="followup_user",
        input_query="今晚找个安静地方待一会儿",
        inferred_context=GroupContext(input_query="今晚找个安静地方待一会儿"),
        plan_candidates=[_candidate(*pois)],
        recommended_plan_id="plan_a",
    )


def test_place_feedback_repository_summarizes_and_rejects_path_traversal(tmp_path) -> None:
    repo = PlaceFeedbackRepository(tmp_path)

    repo.add_feedback(
        PlaceFeedbackRecord(
            session_id="sess",
            user_id="user",
            poi_id="poi_book",
            rating=5,
            tags=["安静", "会再去"],
            raw_feedback="环境很好",
        )
    )
    repo.add_feedback(
        PlaceFeedbackRecord(
            session_id="sess",
            user_id="user",
            poi_id="poi_book",
            rating=2,
            tags=["排队"],
            raw_feedback="排队太久",
        )
    )

    summary = repo.get_summary("poi_book")

    assert summary.feedback_count == 2
    assert summary.avg_rating == 3.5
    assert summary.positive_count == 1
    assert summary.negative_count == 1
    assert summary.tag_counts["安静"] == 1
    with pytest.raises(ValueError):
        repo.get_summary("../poi_book")


def test_confirm_plan_schedules_followup_and_response_updates_memory_and_places(tmp_path) -> None:
    store = SessionStore()
    memory_repo = UserMemoryRepository(tmp_path)
    place_repo = PlaceFeedbackRepository(tmp_path)
    followup_repo = FeedbackFollowupRepository(tmp_path)
    feedback_service = FeedbackService(
        session_store=store,
        memory_update_service=MemoryUpdateService(memory_repo),
    )
    followup_service = FeedbackFollowupService(
        session_store=store,
        repository=followup_repo,
        place_feedback_repository=place_repo,
        feedback_service=feedback_service,
    )
    plan_service = PlanService(
        session_store=store,
        feedback_followup_service=followup_service,
    )
    saved = store.save(_plan(_poi("poi_book", "书店", "安静书店")))

    confirmed = plan_service.confirm_plan(saved.session_id)
    task = followup_service.get_for_session(saved.session_id)

    assert confirmed.state == PlanState.CONFIRMED
    assert task is not None
    assert task.status == "scheduled"
    assert task.places[0].poi_id == "poi_book"
    assert any(question.target == "place" for question in task.questions)

    response = followup_service.submit_response(
        saved.session_id,
        FeedbackFollowupSubmitRequest(
            rating=5,
            raw_feedback="整体很好，安排轻松",
            planning_reasonableness_rating=5,
            planning_feedback="时间和转场都合理",
            place_feedback=[
                PlaceFeedbackSubmitRequest(
                    poi_id="poi_book",
                    rating=5,
                    raw_feedback="很安静，座位舒服，下次还想来",
                    tags=["安静", "会再去"],
                    would_return=True,
                )
            ],
        ),
    )
    memory = memory_repo.get_or_create("followup_user")
    place_summary = place_repo.get_summary("poi_book")

    assert response.success is True
    assert response.task.status == "completed"
    assert "poi_book" in memory.preferences.liked_poi_ids
    assert memory.preferences.category_weights["书店"] == 1.1
    assert place_summary.feedback_count == 1
    assert place_summary.avg_rating == 5


def test_poi_repository_reads_place_feedback_for_ranking_and_detail(tmp_path) -> None:
    data_dir = tmp_path
    records = [
        {
            "id": "poi_a",
            "name": "普通书店",
            "category": "书店",
            "city": "深圳",
            "lon": 114.0,
            "lat": 22.5,
            "avg_price": 20,
            "queue_risk": "low",
            "mood_tags": ["安静"],
            "activity_tags": ["聊天"],
        },
        {
            "id": "poi_b",
            "name": "高分书店",
            "category": "书店",
            "city": "深圳",
            "lon": 114.1,
            "lat": 22.6,
            "avg_price": 30,
            "queue_risk": "low",
            "mood_tags": ["安静"],
            "activity_tags": ["聊天"],
        },
    ]
    (data_dir / "poi.sample.json").write_text(
        json.dumps(records, ensure_ascii=False),
        encoding="utf-8",
    )
    place_repo = PlaceFeedbackRepository(data_dir)
    place_repo.add_feedback(
        PlaceFeedbackRecord(
            session_id="sess",
            user_id="user",
            poi_id="poi_a",
            rating=1,
            raw_feedback="太吵了",
        )
    )
    place_repo.add_feedback(
        PlaceFeedbackRecord(
            session_id="sess",
            user_id="user",
            poi_id="poi_b",
            rating=5,
            raw_feedback="很安静",
        )
    )
    repository = POIRepository(data_dir, place_feedback_repository=place_repo)

    results = repository.search(city="深圳", categories=["书店"], tags=["安静"], limit=2)
    detail = repository.get("poi_b")

    assert [poi.id for poi in results] == ["poi_b", "poi_a"]
    assert detail is not None
    assert detail.business_rules["user_feedback_summary"]["avg_rating"] == 5
