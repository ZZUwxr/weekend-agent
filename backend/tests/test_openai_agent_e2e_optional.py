from __future__ import annotations

import os
from datetime import datetime

import pytest

from local_explorer_agent.app.api import deps
from local_explorer_agent.app.domain.enums import PlanState
from local_explorer_agent.app.domain.models import PlanCandidate, PlanOutput
from local_explorer_agent.app.domain.schemas import PlanPreviewRequest, PlanRevisionRequest


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_OPENAI_AGENT_E2E") != "1" or not os.getenv("LLM_API_KEY"),
    reason="Set RUN_OPENAI_AGENT_E2E=1 and LLM_API_KEY to run real OpenAI Agent E2E tests.",
)


def _clear_deps() -> None:
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


@pytest.fixture()
def service(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("AGENT_RUNTIME", "react")
    monkeypatch.setenv("LLM_ALLOW_RULE_BASED_FALLBACK", "true")
    monkeypatch.setenv("LLM_API_STYLE", "chat_completions")
    monkeypatch.setenv("LLM_TRUST_ENV", os.getenv("LLM_TRUST_ENV", "false"))
    _clear_deps()
    try:
        yield deps.get_plan_service()
    finally:
        _clear_deps()


def _request(query: str, *, duration: int = 300) -> PlanPreviewRequest:
    return PlanPreviewRequest(
        user_id="openai_e2e_user",
        query=query,
        city="深圳",
        start_time=datetime.fromisoformat("2026-05-10T19:00:00"),
        duration_minutes=duration,
    )


def _recommended(plan: PlanOutput) -> PlanCandidate:
    return next(
        candidate
        for candidate in plan.plan_candidates
        if candidate.plan_id == plan.recommended_plan_id
    )


def _categories(candidate: PlanCandidate) -> list[str]:
    return [
        stage.selected_poi.category
        for stage in candidate.stages
        if stage.selected_poi is not None
    ]


def test_openai_agent_barbeque_only(service) -> None:
    plan = service.preview_plan(_request("今晚只想和朋友去吃烧烤，别安排别的", duration=180))
    recommended = _recommended(plan)

    assert plan.state == PlanState.PREVIEW
    assert "烧烤" in _categories(recommended)
    assert len(recommended.stages) <= 2


def test_openai_agent_negated_barbeque_revision(service) -> None:
    plan = service.preview_plan(_request("今晚只想和朋友去吃烧烤，别安排别的", duration=180))
    response = service.revise_plan(
        plan.session_id,
        PlanRevisionRequest(
            message="不想吃烧烤了，换个清淡一点的",
            target_plan_id=plan.recommended_plan_id,
        ),
    )
    recommended = _recommended(response.plan)

    assert "烧烤" not in _categories(recommended)
    assert "烤肉" not in _categories(recommended)
    assert response.revision.patches
    assert "避开烧烤" in response.revision.summary or "清淡" in response.revision.summary


def test_openai_agent_compound_barbeque_then_drink(service) -> None:
    plan = service.preview_plan(_request("今晚只想跟朋友去看个展，别安排别的"))
    response = service.revise_plan(
        plan.session_id,
        PlanRevisionRequest(
            message="吃烧烤之后想去喝酒",
            target_plan_id=plan.recommended_plan_id,
        ),
    )
    categories = _categories(_recommended(response.plan))

    assert "烧烤" in categories
    assert "小酒馆" in categories
    assert categories.index("小酒馆") > categories.index("烧烤")


def test_openai_agent_add_chat_before_barbeque(service) -> None:
    plan = service.preview_plan(_request("今晚只想和朋友去吃烧烤，别安排别的"))
    response = service.revise_plan(
        plan.session_id,
        PlanRevisionRequest(
            message="在吃烧烤之前加一个适合聊天的地方",
            target_plan_id=plan.recommended_plan_id,
        ),
    )
    categories = _categories(_recommended(response.plan))
    chat_indexes = [
        idx for idx, category in enumerate(categories) if category in {"咖啡", "茶馆", "书店"}
    ]

    assert "烧烤" in categories
    assert chat_indexes
    assert chat_indexes[0] < categories.index("烧烤")
    assert response.revision.patches[0].new_value["anchor"] == "before_dining"


def test_openai_agent_cancel_drink_replace_with_barbeque(service) -> None:
    plan = service.preview_plan(_request("今晚只想跟朋友去看个展，别安排别的"))
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
    categories = _categories(_recommended(with_barbeque.plan))
    patch_types = [patch.patch_type for patch in with_barbeque.revision.patches]

    assert "remove_followup_stage" in patch_types
    assert "add_dining_stage" in patch_types or "replace_dining_stage" in patch_types
    assert "小酒馆" not in categories
    assert "烧烤" in categories


def test_openai_agent_family_low_cal_barbeque_has_warning_or_alternative(service) -> None:
    plan = service.preview_plan(_request("带孩子和老婆出门，老婆在减脂，想吃烧烤"))
    recommended = _recommended(plan)
    text = " ".join(
        [
            plan.share_message,
            *plan.assumptions,
            *[
                value
                for candidate in plan.plan_candidates
                for value in (
                    candidate.tradeoff_summary,
                    candidate.recommendation_reason,
                )
                if value
            ],
        ]
    )

    assert recommended.stages
    assert (
        "烧烤" not in _categories(recommended)
        or any(term in text for term in ("减脂", "低卡", "清淡", "补偿", "提醒"))
    )


def test_openai_agent_vague_query_safe_default_or_clarifies(service) -> None:
    plan = service.preview_plan(_request("周末出去玩一下", duration=240))

    assert plan.state in {PlanState.PREVIEW, PlanState.CLARIFYING}
    body = plan.model_dump_json()
    assert "亲子空间" not in body
    assert "孩子" not in body
    assert "情侣" not in body
