from __future__ import annotations

from datetime import datetime

from fastapi.testclient import TestClient

from local_explorer_agent.app.api import deps
from local_explorer_agent.app.domain.enums import PlanState
from local_explorer_agent.app.domain.schemas import (
    ClarificationAnswerRequest,
    PlanPreviewRequest,
    PlanRevisionRequest,
)
from local_explorer_agent.app.main import app


def _clear_all_deps_caches() -> None:
    for fn_name in (
        "get_settings",
        "get_llm_client",
        "get_json_prompt_runner",
        "get_plan_service",
        "get_orchestrator",
        "get_react_runtime",
        "get_poi_repository",
        "get_route_repository",
        "get_queue_repository",
        "get_weather_repository",
        "get_booking_repository",
        "get_poi_tool",
        "get_poi_query_tool",
        "get_route_tool",
        "get_queue_tool",
        "get_weather_tool",
        "get_execution_service",
        "get_feedback_service",
    ):
        fn = getattr(deps, fn_name, None)
        if fn is not None and hasattr(fn, "cache_clear"):
            fn.cache_clear()


def _request(query: str) -> PlanPreviewRequest:
    return PlanPreviewRequest(
        user_id="u_interactive",
        query=query,
        city="深圳",
        start_time=datetime.fromisoformat("2026-05-10T14:00:00"),
        duration_minutes=240,
    )


def _service(monkeypatch):
    monkeypatch.setenv("AGENT_RUNTIME", "react")
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    _clear_all_deps_caches()
    return deps.get_plan_service()


def _preview_plan(monkeypatch):
    service = _service(monkeypatch)
    plan = service.preview_plan(_request("今天下午想和老婆孩子出去玩几小时，别太远，孩子5岁"))
    return service, plan


def test_clarification_required_for_ambiguous_query(monkeypatch) -> None:
    service = _service(monkeypatch)

    plan = service.preview_plan(_request("周末出去玩一下"))

    assert plan.state == PlanState.CLARIFYING
    assert plan.clarification is not None
    assert plan.clarification.needs_clarification is True
    assert len(plan.clarification.questions) <= 3
    assert any(question.required for question in plan.clarification.questions)


def test_safe_assumptions_continue_when_query_says_you_decide(monkeypatch) -> None:
    service = _service(monkeypatch)

    plan = service.preview_plan(_request("你看着安排，别太累"))

    assert plan.state == PlanState.PREVIEW
    assert plan.plan_candidates
    assert plan.assumptions
    assert any("安全默认假设" in item for item in plan.assumptions)


def test_answer_clarification_continues_to_preview(monkeypatch) -> None:
    service = _service(monkeypatch)
    plan = service.preview_plan(_request("周末出去玩一下"))

    updated = service.answer_clarifications(
        plan.session_id,
        ClarificationAnswerRequest(
            answers=[
                {"question_id": "q_activity_style", "answer": "室内轻松"},
                {"question_id": "q_group", "answer": "家庭"},
            ]
        ),
    )

    assert updated.state == PlanState.PREVIEW
    assert updated.plan_candidates
    assert updated.recommended_plan_id


def test_revise_plan_reduce_distance(monkeypatch) -> None:
    service, plan = _preview_plan(monkeypatch)

    response = service.revise_plan(
        plan.session_id,
        PlanRevisionRequest(
            message="第二个地方太远了，换一个近一点、不要排队的",
            target_plan_id=plan.recommended_plan_id,
        ),
    )
    state = service.react_runtime.last_state

    assert response.plan.plan_version == plan.plan_version + 1
    assert response.plan.state == PlanState.PREVIEW
    assert response.revision.patches
    assert state is not None
    assert state.validation_result is not None
    assert state.scoring_completed is True


def test_revise_plan_avoid_queue(monkeypatch) -> None:
    service, plan = _preview_plan(monkeypatch)

    response = service.revise_plan(
        plan.session_id,
        PlanRevisionRequest(
            message="不想排队，帮我换一个等候少一点的地方",
            target_plan_id=plan.recommended_plan_id,
        ),
    )
    state = service.react_runtime.last_state

    assert response.revision.patches
    assert state is not None
    assert any(obs.tool_name == "queue_lookup" for obs in state.observations)
    assert all(
        patch.new_value is None or patch.new_value.get("queue_risk") != "high"
        for patch in response.revision.patches
    )


def test_revise_plan_prefer_indoor(monkeypatch) -> None:
    service, plan = _preview_plan(monkeypatch)

    response = service.revise_plan(
        plan.session_id,
        PlanRevisionRequest(
            message="换成室内，别晒也别淋雨",
            target_plan_id=plan.recommended_plan_id,
        ),
    )

    assert response.revision.patches
    assert any(
        patch.new_value is not None and patch.new_value.get("indoor") is True
        for patch in response.revision.patches
    )


def test_revise_dinner_to_hotpot_targets_dining_stage(monkeypatch) -> None:
    service, plan = _preview_plan(monkeypatch)
    original = next(
        candidate
        for candidate in plan.plan_candidates
        if candidate.plan_id == plan.recommended_plan_id
    )
    original_first_poi_id = original.stages[0].selected_poi.id

    response = service.revise_plan(
        plan.session_id,
        PlanRevisionRequest(
            message="把晚饭换成火锅",
            target_plan_id=plan.recommended_plan_id,
        ),
    )
    revised = next(
        candidate
        for candidate in response.plan.plan_candidates
        if candidate.plan_id == plan.recommended_plan_id
    )
    dining_stage = next(stage for stage in revised.stages if stage.stage_type == "dine")

    assert response.revision.patches
    assert response.revision.patches[0].patch_type == "replace_dining_stage"
    assert "火锅" in response.revision.summary
    assert "原因" in response.revision.summary
    assert dining_stage.selected_poi is not None
    assert dining_stage.selected_poi.category == "火锅"
    assert revised.stages[0].selected_poi is not None
    assert revised.stages[0].selected_poi.id == original_first_poi_id


def test_revise_dinner_to_unsupported_cuisine_still_uses_dining_poi(monkeypatch) -> None:
    service, plan = _preview_plan(monkeypatch)

    response = service.revise_plan(
        plan.session_id,
        PlanRevisionRequest(
            message="把晚饭换成日料",
            target_plan_id=plan.recommended_plan_id,
        ),
    )
    revised = next(
        candidate
        for candidate in response.plan.plan_candidates
        if candidate.plan_id == plan.recommended_plan_id
    )
    dining_stage = next(stage for stage in revised.stages if stage.stage_type == "dine")

    assert response.revision.patches
    assert response.revision.patches[0].patch_type == "replace_dining_stage"
    assert dining_stage.selected_poi is not None
    assert dining_stage.selected_poi.category in {"餐厅", "轻食", "火锅", "日料"}
    assert dining_stage.selected_poi.category != "公园"
    assert "日料" in response.revision.summary


def test_revise_add_hotpot_dinner_when_plan_has_no_dining(monkeypatch) -> None:
    service = _service(monkeypatch)
    plan = service.preview_plan(
        PlanPreviewRequest(
            user_id="u_interactive",
            query="今晚只想跟朋友去看个展，别安排别的",
            city="深圳",
            start_time=datetime.fromisoformat("2026-05-10T19:00:00"),
            duration_minutes=180,
        )
    )
    original = next(
        candidate
        for candidate in plan.plan_candidates
        if candidate.plan_id == plan.recommended_plan_id
    )
    assert all(stage.stage_type != "dine" for stage in original.stages)

    response = service.revise_plan(
        plan.session_id,
        PlanRevisionRequest(
            message="现在想加一个晚饭，吃火锅",
            target_plan_id=plan.recommended_plan_id,
        ),
    )
    revised = next(
        candidate
        for candidate in response.plan.plan_candidates
        if candidate.plan_id == plan.recommended_plan_id
    )
    dining_stages = [stage for stage in revised.stages if stage.stage_type == "dine"]

    assert response.revision.patches
    assert response.revision.patches[0].patch_type == "add_dining_stage"
    assert "新增" in response.revision.summary
    assert "火锅" in response.revision.summary
    assert "原因" in response.revision.summary
    assert len(revised.stages) == len(original.stages) + 1
    assert dining_stages
    assert dining_stages[0].selected_poi is not None
    assert dining_stages[0].selected_poi.category == "火锅"


def test_revise_add_tavern_after_added_dinner(monkeypatch) -> None:
    service = _service(monkeypatch)
    plan = service.preview_plan(
        PlanPreviewRequest(
            user_id="u_interactive",
            query="今晚只想跟朋友去看个展，别安排别的",
            city="深圳",
            start_time=datetime.fromisoformat("2026-05-10T19:00:00"),
            duration_minutes=240,
        )
    )

    with_dinner = service.revise_plan(
        plan.session_id,
        PlanRevisionRequest(
            message="看完展之后想吃桑拿鸡",
            target_plan_id=plan.recommended_plan_id,
        ),
    )
    dinner_plan = next(
        candidate
        for candidate in with_dinner.plan.plan_candidates
        if candidate.plan_id == with_dinner.plan.recommended_plan_id
    )
    assert sum(1 for stage in dinner_plan.stages if stage.stage_type == "dine") == 1
    assert any(
        stage.selected_poi and stage.selected_poi.category == "桑拿鸡"
        for stage in dinner_plan.stages
    )

    with_tavern = service.revise_plan(
        with_dinner.plan.session_id,
        PlanRevisionRequest(
            message="吃完饭之后安排一个小酒馆",
            target_plan_id=with_dinner.plan.recommended_plan_id,
        ),
    )
    revised = next(
        candidate
        for candidate in with_tavern.plan.plan_candidates
        if candidate.plan_id == with_tavern.plan.recommended_plan_id
    )
    dining_indexes = [idx for idx, stage in enumerate(revised.stages) if stage.stage_type == "dine"]
    tavern_indexes = [
        idx
        for idx, stage in enumerate(revised.stages)
        if stage.selected_poi is not None and stage.selected_poi.category == "小酒馆"
    ]

    assert with_tavern.revision.patches
    assert with_tavern.revision.patches[0].patch_type == "add_followup_stage"
    assert "小酒馆" in with_tavern.revision.summary
    assert len(dining_indexes) == 1
    assert tavern_indexes
    assert tavern_indexes[0] > dining_indexes[0]

    tavern_stage = revised.stages[tavern_indexes[0]]
    old_tavern_id = tavern_stage.selected_poi.id
    replaced_tavern = service.revise_plan(
        with_tavern.plan.session_id,
        PlanRevisionRequest(
            message="小酒馆太吵了，换一家安静点的",
            target_plan_id=with_tavern.plan.recommended_plan_id,
        ),
    )
    replaced = next(
        candidate
        for candidate in replaced_tavern.plan.plan_candidates
        if candidate.plan_id == replaced_tavern.plan.recommended_plan_id
    )
    tavern_stages = [
        stage
        for stage in replaced.stages
        if stage.selected_poi is not None and stage.selected_poi.category == "小酒馆"
    ]

    assert replaced_tavern.revision.patches
    assert replaced_tavern.revision.patches[0].patch_type == "replace_followup_stage"
    assert len(tavern_stages) == 1
    assert tavern_stages[0].selected_poi.id != old_tavern_id
    assert sum(1 for stage in replaced.stages if stage.stage_type == "dine") == 1

    current_tavern_id = tavern_stages[0].selected_poi.id
    generic_replaced_tavern = service.revise_plan(
        replaced_tavern.plan.session_id,
        PlanRevisionRequest(
            message="换个地方，离饭店近一点",
            target_plan_id=replaced_tavern.plan.recommended_plan_id,
        ),
    )
    generic_replaced = next(
        candidate
        for candidate in generic_replaced_tavern.plan.plan_candidates
        if candidate.plan_id == generic_replaced_tavern.plan.recommended_plan_id
    )
    generic_tavern_stages = [
        stage
        for stage in generic_replaced.stages
        if stage.selected_poi is not None and stage.selected_poi.category == "小酒馆"
    ]

    assert generic_replaced_tavern.revision.patches
    assert generic_replaced_tavern.revision.patches[0].patch_type == "replace_followup_stage"
    assert len(generic_tavern_stages) == 1
    assert generic_tavern_stages[0].selected_poi.id != current_tavern_id
    assert sum(1 for stage in generic_replaced.stages if stage.stage_type == "dine") == 1


def test_revise_followup_to_different_category_replaces_stage(monkeypatch) -> None:
    service = _service(monkeypatch)
    plan = service.preview_plan(
        PlanPreviewRequest(
            user_id="u_interactive",
            query="今晚只想跟朋友去看个展，别安排别的",
            city="深圳",
            start_time=datetime.fromisoformat("2026-05-10T19:00:00"),
            duration_minutes=300,
        )
    )
    with_tavern = service.revise_plan(
        plan.session_id,
        PlanRevisionRequest(
            message="看完展想去喝个酒",
            target_plan_id=plan.recommended_plan_id,
        ),
    )
    tavern_plan = next(
        candidate
        for candidate in with_tavern.plan.plan_candidates
        if candidate.plan_id == with_tavern.plan.recommended_plan_id
    )

    with_coffee = service.revise_plan(
        with_tavern.plan.session_id,
        PlanRevisionRequest(
            message="小酒馆太吵了，换成喝咖啡吧",
            target_plan_id=with_tavern.plan.recommended_plan_id,
        ),
    )
    revised = next(
        candidate
        for candidate in with_coffee.plan.plan_candidates
        if candidate.plan_id == with_coffee.plan.recommended_plan_id
    )

    assert [patch.patch_type for patch in with_coffee.revision.patches] == [
        "replace_followup_stage"
    ]
    assert len(revised.stages) == len(tavern_plan.stages)
    assert any(
        stage.selected_poi is not None and stage.selected_poi.category == "咖啡"
        for stage in revised.stages
    )
    assert all(
        stage.selected_poi is None or stage.selected_poi.category != "小酒馆"
        for stage in revised.stages
    )
    assert "咖啡" in with_coffee.revision.summary
    assert revised.timeline


def test_revise_compound_barbeque_then_drink(monkeypatch) -> None:
    service = _service(monkeypatch)
    plan = service.preview_plan(
        PlanPreviewRequest(
            user_id="u_interactive",
            query="今晚只想跟朋友去看个展，别安排别的",
            city="深圳",
            start_time=datetime.fromisoformat("2026-05-10T19:00:00"),
            duration_minutes=300,
        )
    )

    response = service.revise_plan(
        plan.session_id,
        PlanRevisionRequest(
            message="吃烧烤之后想去喝酒",
            target_plan_id=plan.recommended_plan_id,
        ),
    )
    revised = next(
        candidate
        for candidate in response.plan.plan_candidates
        if candidate.plan_id == response.plan.recommended_plan_id
    )
    dining_indexes = [idx for idx, stage in enumerate(revised.stages) if stage.stage_type == "dine"]
    tavern_indexes = [
        idx
        for idx, stage in enumerate(revised.stages)
        if stage.selected_poi is not None and stage.selected_poi.category == "小酒馆"
    ]
    patch_types = [patch.patch_type for patch in response.revision.patches]

    assert "add_dining_stage" in patch_types or "replace_dining_stage" in patch_types
    assert "add_followup_stage" in patch_types
    assert dining_indexes
    assert tavern_indexes
    assert tavern_indexes[0] > dining_indexes[0]
    assert revised.stages[dining_indexes[0]].selected_poi is not None
    assert revised.stages[dining_indexes[0]].selected_poi.category == "烧烤"
    assert "小酒馆" in response.revision.summary


def test_revise_negated_barbeque_replaces_with_non_barbeque(monkeypatch) -> None:
    service = _service(monkeypatch)
    plan = service.preview_plan(
        PlanPreviewRequest(
            user_id="u_interactive",
            query="今晚只想跟朋友去看个展，别安排别的",
            city="深圳",
            start_time=datetime.fromisoformat("2026-05-10T19:00:00"),
            duration_minutes=300,
        )
    )
    with_barbeque = service.revise_plan(
        plan.session_id,
        PlanRevisionRequest(
            message="吃烧烤之后想去喝酒",
            target_plan_id=plan.recommended_plan_id,
        ),
    )

    without_barbeque = service.revise_plan(
        with_barbeque.plan.session_id,
        PlanRevisionRequest(
            message="不想吃烧烤了",
            target_plan_id=with_barbeque.plan.recommended_plan_id,
        ),
    )
    revised = next(
        candidate
        for candidate in without_barbeque.plan.plan_candidates
        if candidate.plan_id == without_barbeque.plan.recommended_plan_id
    )
    dining_stage = next(stage for stage in revised.stages if stage.stage_type == "dine")

    assert without_barbeque.revision.patches
    assert without_barbeque.revision.patches[0].patch_type == "replace_dining_stage"
    assert without_barbeque.revision.patches[0].old_value["category"] == "烧烤"
    assert dining_stage.selected_poi is not None
    assert dining_stage.selected_poi.category != "烧烤"
    assert "避开烧烤" in without_barbeque.revision.summary


def test_revise_add_chat_before_barbeque(monkeypatch) -> None:
    service = _service(monkeypatch)
    plan = service.preview_plan(
        PlanPreviewRequest(
            user_id="u_interactive",
            query="今晚只想和朋友去吃烧烤，别安排别的",
            city="深圳",
            start_time=datetime.fromisoformat("2026-05-10T19:00:00"),
            duration_minutes=240,
        )
    )

    response = service.revise_plan(
        plan.session_id,
        PlanRevisionRequest(
            message="在吃烧烤之前加一个适合聊天的地方",
            target_plan_id=plan.recommended_plan_id,
        ),
    )
    revised = next(
        candidate
        for candidate in response.plan.plan_candidates
        if candidate.plan_id == response.plan.recommended_plan_id
    )
    dining_indexes = [
        idx
        for idx, stage in enumerate(revised.stages)
        if stage.selected_poi is not None and stage.selected_poi.category == "烧烤"
    ]
    chat_indexes = [
        idx
        for idx, stage in enumerate(revised.stages)
        if stage.selected_poi is not None and stage.selected_poi.category in {"咖啡", "茶馆", "书店"}
    ]

    assert response.revision.patches
    assert response.revision.patches[0].patch_type == "add_followup_stage"
    assert dining_indexes
    assert chat_indexes
    assert chat_indexes[0] < dining_indexes[0]
    assert response.revision.patches[0].new_value["anchor"] == "before_dining"
    assert response.revision.patches[0].new_value["category"] in {"咖啡", "茶馆", "书店"}
    assert response.revision.patches[0].new_value["requested_category"] == "聊天"
    assert "用餐前" in response.revision.summary
    assert "饭后" not in response.revision.summary
    assert "行程末尾" not in response.revision.summary
    assert "用餐前" in response.revision.patches[0].reason
    chat_stage = revised.stages[chat_indexes[0]]
    assert "饭后" not in " ".join([chat_stage.name, chat_stage.experience_goal, chat_stage.reasoning])
    assert "行程末尾" not in " ".join([chat_stage.name, chat_stage.experience_goal, chat_stage.reasoning])
    assert revised.timeline


def test_preview_exhibition_then_chat_keeps_two_explicit_stages(monkeypatch) -> None:
    service = _service(monkeypatch)

    plan = service.preview_plan(_request("周末想和朋友看展，再找个地方聊天"))
    recommended = next(
        candidate
        for candidate in plan.plan_candidates
        if candidate.plan_id == plan.recommended_plan_id
    )

    assert "只安排这一个" not in recommended.title
    assert len(recommended.stages) >= 2
    assert any(
        stage.selected_poi is not None and stage.selected_poi.category == "展览"
        for stage in recommended.stages
    )
    assert any(
        "聊天" in stage.name or "聊天" in stage.experience_goal for stage in recommended.stages
    )
    assert recommended.timeline


def test_replace_cancelled_drink_with_barbeque_removes_tavern(monkeypatch) -> None:
    service = _service(monkeypatch)
    plan = service.preview_plan(
        PlanPreviewRequest(
            user_id="u_interactive",
            query="周末想和朋友看展，再找个地方聊天",
            city="深圳",
            start_time=datetime.fromisoformat("2026-05-10T19:00:00"),
            duration_minutes=300,
        )
    )
    with_drink = service.revise_plan(
        plan.session_id,
        PlanRevisionRequest(
            message="看完展想去喝个酒",
            target_plan_id=plan.recommended_plan_id,
        ),
    )

    with_barbeque = service.revise_plan(
        with_drink.plan.session_id,
        PlanRevisionRequest(
            message="不想去喝酒了，换成吃烧烤吧",
            target_plan_id=with_drink.plan.recommended_plan_id,
        ),
    )
    revised = next(
        candidate
        for candidate in with_barbeque.plan.plan_candidates
        if candidate.plan_id == with_barbeque.plan.recommended_plan_id
    )
    patch_types = [patch.patch_type for patch in with_barbeque.revision.patches]

    assert "remove_followup_stage" in patch_types
    assert "add_dining_stage" in patch_types or "replace_dining_stage" in patch_types
    assert any(
        stage.selected_poi is not None and stage.selected_poi.category == "烧烤"
        for stage in revised.stages
    )
    assert all(
        stage.selected_poi is None or stage.selected_poi.category != "小酒馆"
        for stage in revised.stages
    )
    assert "取消" in with_barbeque.revision.summary
    assert "烧烤" in with_barbeque.revision.summary
    assert revised.timeline


def test_replace_cancelled_drink_with_coffee_adds_new_followup(monkeypatch) -> None:
    service = _service(monkeypatch)
    plan = service.preview_plan(
        PlanPreviewRequest(
            user_id="u_interactive",
            query="今晚只想跟朋友去看个展，别安排别的",
            city="深圳",
            start_time=datetime.fromisoformat("2026-05-10T19:00:00"),
            duration_minutes=300,
        )
    )
    with_drink = service.revise_plan(
        plan.session_id,
        PlanRevisionRequest(
            message="看完展想去喝个酒",
            target_plan_id=plan.recommended_plan_id,
        ),
    )

    with_coffee = service.revise_plan(
        with_drink.plan.session_id,
        PlanRevisionRequest(
            message="不想去喝酒了，换成喝咖啡吧",
            target_plan_id=with_drink.plan.recommended_plan_id,
        ),
    )
    revised = next(
        candidate
        for candidate in with_coffee.plan.plan_candidates
        if candidate.plan_id == with_coffee.plan.recommended_plan_id
    )
    patch_types = [patch.patch_type for patch in with_coffee.revision.patches]

    assert patch_types == ["remove_followup_stage", "add_followup_stage"]
    assert any(
        stage.selected_poi is not None and stage.selected_poi.category == "咖啡"
        for stage in revised.stages
    )
    assert all(
        stage.selected_poi is None or stage.selected_poi.category != "小酒馆"
        for stage in revised.stages
    )
    assert "取消" in with_coffee.revision.summary
    assert "咖啡" in with_coffee.revision.summary
    assert revised.timeline


def test_cancel_drink_removes_tavern_without_extra_patch(monkeypatch) -> None:
    service = _service(monkeypatch)
    plan = service.preview_plan(
        PlanPreviewRequest(
            user_id="u_interactive",
            query="今晚只想跟朋友去看个展，别安排别的",
            city="深圳",
            start_time=datetime.fromisoformat("2026-05-10T19:00:00"),
            duration_minutes=240,
        )
    )
    with_drink = service.revise_plan(
        plan.session_id,
        PlanRevisionRequest(
            message="看完展想去喝个酒",
            target_plan_id=plan.recommended_plan_id,
        ),
    )
    cancelled = service.revise_plan(
        with_drink.plan.session_id,
        PlanRevisionRequest(
            message="喝酒取消呀",
            target_plan_id=with_drink.plan.recommended_plan_id,
        ),
    )
    revised = next(
        candidate
        for candidate in cancelled.plan.plan_candidates
        if candidate.plan_id == cancelled.plan.recommended_plan_id
    )

    assert [patch.patch_type for patch in cancelled.revision.patches] == ["remove_followup_stage"]
    assert all(
        stage.selected_poi is None or stage.selected_poi.category != "小酒馆"
        for stage in revised.stages
    )
    assert "取消" in cancelled.revision.summary
    assert revised.timeline


def test_cancel_drink_when_no_tavern_is_noop(monkeypatch) -> None:
    service = _service(monkeypatch)
    plan = service.preview_plan(
        PlanPreviewRequest(
            user_id="u_interactive",
            query="周末想和朋友看展，再找个地方聊天",
            city="深圳",
            start_time=datetime.fromisoformat("2026-05-10T19:00:00"),
            duration_minutes=300,
        )
    )
    with_drink = service.revise_plan(
        plan.session_id,
        PlanRevisionRequest(
            message="看完展想去喝个酒",
            target_plan_id=plan.recommended_plan_id,
        ),
    )
    with_barbeque = service.revise_plan(
        with_drink.plan.session_id,
        PlanRevisionRequest(
            message="不想去喝酒了，换成吃烧烤吧",
            target_plan_id=with_drink.plan.recommended_plan_id,
        ),
    )

    cancelled_again = service.revise_plan(
        with_barbeque.plan.session_id,
        PlanRevisionRequest(
            message="喝酒取消呀",
            target_plan_id=with_barbeque.plan.recommended_plan_id,
        ),
    )
    revised = next(
        candidate
        for candidate in cancelled_again.plan.plan_candidates
        if candidate.plan_id == cancelled_again.plan.recommended_plan_id
    )

    assert cancelled_again.revision.patches == []
    assert any("没有找到可取消" in warning for warning in cancelled_again.revision.warnings)
    assert "新增" not in "；".join(cancelled_again.revision.warnings)
    assert all(
        stage.selected_poi is None or stage.selected_poi.category != "小酒馆"
        for stage in revised.stages
    )
    assert revised.timeline


def test_locked_item_not_changed_during_revision(monkeypatch) -> None:
    service, plan = _preview_plan(monkeypatch)
    recommended = next(
        candidate
        for candidate in plan.plan_candidates
        if candidate.plan_id == plan.recommended_plan_id
    )
    locked_poi = recommended.stages[1].selected_poi
    assert locked_poi is not None

    response = service.revise_plan(
        plan.session_id,
        PlanRevisionRequest(
            message="第二个地方太远了，换一个近一点",
            target_plan_id=plan.recommended_plan_id,
            locked_items=[{"type": "poi", "id": locked_poi.id, "reason": "这个地方我喜欢，保留"}],
        ),
    )
    revised = next(
        candidate
        for candidate in response.plan.plan_candidates
        if candidate.plan_id == plan.recommended_plan_id
    )

    assert revised.stages[1].selected_poi is not None
    assert revised.stages[1].selected_poi.id == locked_poi.id


def test_confirmed_plan_cannot_be_revised_directly(monkeypatch) -> None:
    service, plan = _preview_plan(monkeypatch)
    service.confirm_plan(plan.session_id)
    client = TestClient(app)

    response = client.post(
        f"/api/v1/plans/{plan.session_id}/revise",
        json={"message": "换成室内", "locked_items": [], "revision_mode": "partial"},
    )

    assert response.status_code == 409
    payload = response.json()
    assert payload["code"] == "http_409"
    assert "confirmed" in payload["message"]


def test_revision_summary_contains_patches(monkeypatch) -> None:
    service, plan = _preview_plan(monkeypatch)

    response = service.revise_plan(
        plan.session_id,
        PlanRevisionRequest(
            message="第二个地方太远了",
            target_plan_id=plan.recommended_plan_id,
        ),
    )

    assert response.revision.summary
    assert response.revision.patches
    assert response.plan.revision_summary is not None


def test_revision_sse_events(monkeypatch) -> None:
    service, plan = _preview_plan(monkeypatch)
    events = []

    response = service.revise_plan(
        plan.session_id,
        PlanRevisionRequest(
            message="第二个地方太远了，换一个近一点",
            target_plan_id=plan.recommended_plan_id,
        ),
        event_callback=events.append,
    )
    names = [event.event for event in events]

    assert response.revision.patches
    assert "revision_started" in names
    assert "plan_patch_applied" in names
    assert "revision_complete" in names


def test_revise_plan_b_preserves_target(monkeypatch) -> None:
    """Revising plan_b should modify plan_b, not plan_a."""
    service, plan = _preview_plan(monkeypatch)
    # Pick plan_b if available, else second candidate
    candidates = plan.plan_candidates
    assert len(candidates) >= 2, "Need at least 2 candidates for this test"
    target = candidates[1]
    target_id = target.plan_id

    response = service.revise_plan(
        plan.session_id,
        PlanRevisionRequest(
            message="第二个地方太远了，换一个近一点的",
            target_plan_id=target_id,
        ),
    )

    revised_target = next(
        (c for c in response.plan.plan_candidates if c.plan_id == target_id),
        None,
    )
    assert revised_target is not None
    # The other candidate should be unchanged
    other = next(
        (c for c in response.plan.plan_candidates if c.plan_id != target_id),
        None,
    )
    if other:
        original_other = next(c for c in plan.plan_candidates if c.plan_id == other.plan_id)
        assert other.stages[0].selected_poi.id == original_other.stages[0].selected_poi.id


def test_revise_unfulfillable_returns_warning(monkeypatch) -> None:
    """When no replacement exists, warnings must explain why."""
    service, plan = _preview_plan(monkeypatch)

    # Request something very specific that's unlikely to have a replacement
    response = service.revise_plan(
        plan.session_id,
        PlanRevisionRequest(
            message="换成室内的天文台，要有海底隧道",
            target_plan_id=plan.recommended_plan_id,
        ),
    )

    # Either patches exist (found something) or warnings explain why not
    if not response.revision.patches:
        assert response.revision.warnings, "Must have warnings when no patches produced"
        assert response.revision.summary
        # Summary must not be the generic "no changes" message
        assert "没有找到需要强制替换" not in response.revision.summary


def test_revise_reduce_distance_produces_real_patch(monkeypatch) -> None:
    """reduce_distance must produce a real replace_poi patch, not just a summary."""
    service, plan = _preview_plan(monkeypatch)

    response = service.revise_plan(
        plan.session_id,
        PlanRevisionRequest(
            message="第二个地方太远了，换一个近一点的",
            target_plan_id=plan.recommended_plan_id,
        ),
    )

    assert response.revision.patches, "reduce_distance must produce patches"
    patch = response.revision.patches[0]
    assert patch.patch_type == "replace_poi"
    assert patch.old_value is not None
    assert patch.new_value is not None
    assert patch.old_value["poi_id"] != patch.new_value["poi_id"]
    assert patch.reason
    # Plan version must increment
    assert response.plan.plan_version == plan.plan_version + 1
    # Validation and scoring must have run
    state = service.react_runtime.last_state
    assert state is not None
    assert state.validation_result is not None
    assert state.scoring_completed is True


def test_revise_avoid_queue_replaces_high_queue_poi(monkeypatch) -> None:
    """avoid_queue should replace high queue_risk POIs or warn."""
    service, plan = _preview_plan(monkeypatch)

    response = service.revise_plan(
        plan.session_id,
        PlanRevisionRequest(
            message="不想排队，帮我换一个等候少一点的地方",
            target_plan_id=plan.recommended_plan_id,
        ),
    )

    if response.revision.patches:
        # If patches produced, new POI must not be high queue
        for patch in response.revision.patches:
            if patch.new_value:
                assert patch.new_value.get("queue_risk") != "high"
    else:
        # If no patches, warnings must explain
        assert response.revision.warnings


def test_revise_prefer_indoor_replaces_outdoor_poi(monkeypatch) -> None:
    """prefer_indoor should replace with indoor=true or warn."""
    service, plan = _preview_plan(monkeypatch)

    response = service.revise_plan(
        plan.session_id,
        PlanRevisionRequest(
            message="换成室内，别晒也别淋雨",
            target_plan_id=plan.recommended_plan_id,
        ),
    )

    if response.revision.patches:
        assert any(
            p.new_value is not None and p.new_value.get("indoor") is True
            for p in response.revision.patches
        )
    else:
        assert response.revision.warnings


def test_locked_item_warning_during_revision(monkeypatch) -> None:
    """When the target stage is locked, revision should warn."""
    service, plan = _preview_plan(monkeypatch)
    recommended = next(c for c in plan.plan_candidates if c.plan_id == plan.recommended_plan_id)
    # Lock ALL stages' POIs
    locked = [
        {"type": "poi", "id": s.selected_poi.id, "reason": "保留"}
        for s in recommended.stages
        if s.selected_poi
    ]

    response = service.revise_plan(
        plan.session_id,
        PlanRevisionRequest(
            message="第二个地方太远了，换一个近一点的",
            target_plan_id=plan.recommended_plan_id,
            locked_items=locked,
        ),
    )

    # All POIs locked → no patches, must have warning
    if not response.revision.patches:
        assert response.revision.warnings or "锁定" in response.revision.summary
