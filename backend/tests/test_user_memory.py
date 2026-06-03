from __future__ import annotations

import asyncio
from datetime import datetime

import pytest

from local_explorer_agent.app.agent.plan_manager import SessionStore
from local_explorer_agent.app.agent.react.actions import AgentActionType
from local_explorer_agent.app.agent.react.factory import build_react_agent_runtime
from local_explorer_agent.app.agent.react.reducer import StateReducer
from local_explorer_agent.app.agent.react.skill_tools import ScoreCandidatesTool
from local_explorer_agent.app.agent.react.state import AgentObservation, AgentState
from local_explorer_agent.app.agent.skills.place_selection import PlaceSelectionSkill
from local_explorer_agent.app.agent.skills.user_understanding import UserUnderstandingSkill
from local_explorer_agent.app.core.config import get_settings
from local_explorer_agent.app.domain.enums import PlanType, StageType
from local_explorer_agent.app.domain.memory import (
    UserMemory,
    UserMemoryCompanion,
    UserMemoryContext,
    UserMemoryFeedback,
    UserMemoryPreferences,
    UserMemoryProfile,
)
from local_explorer_agent.app.domain.models import (
    POI,
    GroupContext,
    PlanCandidate,
    PlanOutput,
    Stage,
)
from local_explorer_agent.app.domain.schemas import FeedbackRequest, PlanPreviewRequest
from local_explorer_agent.app.domain.scoring import choose_recommended_candidate, score_candidate
from local_explorer_agent.app.repositories.poi_repository import POIRepository
from local_explorer_agent.app.repositories.queue_repository import QueueRepository
from local_explorer_agent.app.repositories.user_memory_repository import UserMemoryRepository
from local_explorer_agent.app.repositories.weather_repository import WeatherRepository
from local_explorer_agent.app.services.feedback_service import FeedbackService
from local_explorer_agent.app.services.memory_update_service import MemoryUpdateService
from local_explorer_agent.app.tools.poi_query_tool import POIQueryRewriteTool
from local_explorer_agent.app.tools.poi_tool import POITool
from local_explorer_agent.app.tools.queue_tool import QueueTool
from local_explorer_agent.app.tools.weather_tool import WeatherTool


def _request(user_id: str = "memory_user") -> PlanPreviewRequest:
    return PlanPreviewRequest(
        user_id=user_id,
        query="今天下午想和老婆孩子出去玩几小时，别太远",
        city="深圳",
        start_time=datetime.fromisoformat("2026-05-10T14:00:00"),
        duration_minutes=240,
    )


def _poi(poi_id: str, category: str, tags: list[str] | None = None) -> POI:
    return POI(
        id=poi_id,
        name=f"{category}-{poi_id}",
        category=category,
        city="深圳",
        lon=114.0,
        lat=22.5,
        activity_tags=tags or [],
        mood_tags=tags or [],
    )


def _candidate(plan_id: str, poi: POI) -> PlanCandidate:
    return PlanCandidate(
        plan_id=plan_id,
        plan_type=PlanType.PLAN_A if plan_id == "plan_a" else PlanType.PLAN_B,
        title=plan_id,
        theme="test",
        stages=[
            Stage(
                stage_id=f"stage_{plan_id}",
                stage_type=StageType.EXPLORE,
                name="探索",
                experience_goal="探索",
                duration_minutes=60,
                selected_poi=poi,
                constraints={"categories": [poi.category], "标签": poi.activity_tags},
            )
        ],
    )


def _memory_context() -> UserMemoryContext:
    return UserMemoryContext(
        user_id="memory_user",
        profile=UserMemoryProfile(max_walking_minutes_per_segment=12),
        companions=[
            UserMemoryCompanion(
                companion_id="spouse",
                display_name="老婆",
                role_type="spouse",
                hard_constraints=["餐饮需低负担、低油低糖或轻食可选"],
                soft_preferences=["轻松聊天"],
                risk_points=["低卡需求容易和亲子餐饮便利性冲突"],
            ),
            UserMemoryCompanion(
                companion_id="child_5yo",
                display_name="儿子",
                role_type="child",
                age=5,
                hard_constraints=["适合5岁儿童"],
                soft_preferences=["互动"],
            ),
        ],
        likes=["书店", "安静"],
        dislikes=["排队"],
        category_weights={"书店": 1.6, "烧烤": 0.6},
        tag_weights={"安静": 1.5, "热闹": 0.6},
    )


def test_user_memory_repository_creates_file_and_rejects_path_traversal(tmp_path) -> None:
    repo = UserMemoryRepository(tmp_path)

    memory = repo.get_or_create("memory_user")

    assert memory.user_id == "memory_user"
    assert (tmp_path / "user_memory" / "memory_user.json").exists()
    with pytest.raises(ValueError):
        repo.get_or_create("../evil")


def test_user_memory_repository_round_trip_and_truncates_feedback(tmp_path) -> None:
    repo = UserMemoryRepository(tmp_path)
    memory = UserMemory(
        user_id="memory_user",
        updated_at="2026-05-13T20:00:00+08:00",
        preferences=UserMemoryPreferences(category_weights={"书店": 2.5}),
        feedback_history=[
            UserMemoryFeedback(
                feedback_id=f"fb_{index}",
                session_id="sess",
                rating=5,
                created_at="2026-05-13T20:00:00+08:00",
            )
            for index in range(60)
        ],
    )

    repo.save(memory)
    loaded = repo.get_or_create("memory_user")

    assert loaded.preferences.category_weights["书店"] == 1.8
    assert len(loaded.feedback_history) == 50
    assert loaded.feedback_history[0].feedback_id == "fb_10"


def test_react_registry_includes_read_user_memory(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    runtime = build_react_agent_runtime(
        user_memory_repository=UserMemoryRepository(tmp_path),
    )

    names = {spec.name for spec in runtime.tool_registry.list_specs()}

    assert "read_user_memory" in names


def test_reducer_stores_user_memory_context() -> None:
    state = AgentState(session_id="sess_memory", user_id="memory_user", request=_request())
    observation = AgentObservation(
        action_type=AgentActionType.CALL_TOOL,
        tool_name="read_user_memory",
        success=True,
        data=_memory_context().model_dump(),
    )

    new_state = StateReducer().reduce(
        state,
        action=state.trace[-1].action if state.trace else _dummy_memory_action(),
        observation=observation,
    )

    assert new_state.user_memory is not None
    assert new_state.user_memory.category_weights["书店"] == 1.6


def _dummy_memory_action():
    from local_explorer_agent.app.agent.react.actions import AgentAction

    return AgentAction(
        action_type=AgentActionType.CALL_TOOL,
        tool_name="read_user_memory",
        tool_args={"user_id": "memory_user"},
        decision_summary="read memory",
    )


def test_mock_runtime_reads_memory_before_understanding(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    runtime = build_react_agent_runtime(
        user_memory_repository=UserMemoryRepository(tmp_path),
    )

    asyncio.run(runtime.run(_request()))
    tools = [step.action.tool_name for step in runtime.last_state.trace if step.action.tool_name]

    assert "read_user_memory" in tools
    assert "intake_user_requirements" in tools
    assert tools.index("read_user_memory") < tools.index("understand_user")
    assert tools.index("intake_user_requirements") < tools.index("understand_user")


def test_user_understanding_merges_relevant_memory_companions() -> None:
    context = UserUnderstandingSkill().run(
        user_query="今天下午想和老婆孩子出去玩几小时，别太远",
        user_id="memory_user",
        city="深圳",
        start_time=datetime.fromisoformat("2026-05-10T14:00:00"),
        duration_minutes=240,
        user_memory=_memory_context(),
    )

    spouse = next(role for role in context.roles if role.role_type == "spouse")

    assert "记忆：单段步行不超过12分钟" in context.inferred_constraints
    assert "餐饮需低负担、低油低糖或轻食可选" in spouse.hard_constraints
    assert any(role.age == 5 for role in context.roles if role.role_type == "child")


def test_memory_bias_changes_score_recommendation() -> None:
    state = AgentState(
        session_id="sess_score_memory",
        user_id="memory_user",
        request=_request(),
        inferred_context=GroupContext(
            group_type="solo",
            group_size=1,
            roles=[],
            input_query="周末找个安静地方待一会儿",
        ),
        candidate_plans=[
            _candidate("plan_a", _poi("poi_book", "书店", ["安静"])),
            _candidate("plan_b", _poi("poi_bbq", "烧烤", ["热闹"])),
        ],
        user_memory=_memory_context(),
    )
    tool = ScoreCandidatesTool(
        score_fn=score_candidate,
        choose_fn=choose_recommended_candidate,
    )

    result = asyncio.run(tool.run(tool.args_schema(), state))

    assert result.success is True
    assert result.data["recommended_plan_id"] == "plan_a"
    plan_a = next(item for item in result.data["candidates"] if item["plan_id"] == "plan_a")
    assert "匹配你的历史偏好" in plan_a["recommendation_reason"]


def test_explicit_hotpot_query_overrides_light_food_memory() -> None:
    settings = get_settings()
    data_dir = settings.data_dir if settings.data_dir.is_absolute() else settings.data_dir.resolve()
    poi_repository = POIRepository(data_dir)
    skill = PlaceSelectionSkill(
        poi_query_tool=POIQueryRewriteTool(poi_repository),
        poi_tool=POITool(poi_repository),
        queue_tool=QueueTool(QueueRepository(data_dir)),
        weather_tool=WeatherTool(WeatherRepository(data_dir)),
    )
    context = GroupContext(input_query="今晚只想吃火锅，别安排别的")
    candidate = PlanCandidate(
        plan_id="plan_a",
        plan_type=PlanType.PLAN_A,
        title="火锅",
        theme="火锅",
        stages=[
            Stage(
                stage_id="stage_hotpot",
                stage_type=StageType.DINE,
                name="直奔火锅",
                experience_goal="吃火锅",
                duration_minutes=90,
                constraints={"categories": ["火锅"], "标签": ["火锅"]},
            )
        ],
    )
    memory = UserMemoryContext(
        user_id="memory_user",
        category_weights={"轻食": 1.8, "火锅": 0.5},
        tag_weights={"低卡": 1.8},
    )

    result = skill.run(
        candidate=candidate,
        group_context=context,
        city="深圳",
        start_time=datetime.fromisoformat("2026-05-10T19:00:00"),
        user_memory=memory,
    )

    assert result.stages[0].selected_poi is not None
    assert result.stages[0].selected_poi.category == "火锅"


def test_feedback_service_writes_back_memory(tmp_path) -> None:
    repo = UserMemoryRepository(tmp_path)
    store = SessionStore()
    plan = PlanOutput(
        user_id="memory_user",
        input_query="找个书店待一会儿",
        inferred_context=GroupContext(input_query="找个书店待一会儿"),
        plan_candidates=[_candidate("plan_a", _poi("poi_book", "书店", ["安静"]))],
        recommended_plan_id="plan_a",
    )
    saved = store.save(plan)
    service = FeedbackService(
        session_store=store,
        memory_update_service=MemoryUpdateService(repo),
    )

    service.submit_feedback(
        saved.session_id,
        FeedbackRequest(rating=2, raw_feedback="这个书店太吵了", tags=["too_noisy"]),
    )
    memory = repo.get_or_create("memory_user")

    assert memory.preferences.category_weights["书店"] == 0.85
    assert memory.preferences.tag_weights["热闹"] == 0.85
    assert "poi_book" in memory.preferences.disliked_poi_ids
    assert len(memory.feedback_history) == 1
