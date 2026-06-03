import json
from datetime import datetime

from local_explorer_agent.app.agent.llm.schemas import PlanCandidateListOutput
from local_explorer_agent.app.agent.skills.conflict_detection import ConflictDetectionSkill
from local_explorer_agent.app.agent.skills.experience_planning import ExperiencePlanningSkill
from local_explorer_agent.app.agent.skills.negotiation import NegotiationSkill
from local_explorer_agent.app.agent.skills.user_understanding import UserUnderstandingSkill
from local_explorer_agent.app.domain.enums import PlanType, StageType
from local_explorer_agent.app.domain.models import PlanCandidate, Stage


def _build_inputs(query: str):
    context = UserUnderstandingSkill().run(
        user_query=query,
        user_id="u-test",
        city="深圳",
        start_time=datetime.fromisoformat("2026-05-11T14:00:00"),
        duration_minutes=240,
    )
    conflicts = ConflictDetectionSkill().run(context)
    strategies = NegotiationSkill().run(group_context=context, conflicts=conflicts)
    return context, conflicts, strategies


def test_experience_planning_family_demo_stages_reference_roles() -> None:
    context, conflicts, strategies = _build_inputs(
        "今天下午想和老婆孩子出去玩几小时，别太远，老婆最近在减肥，孩子5岁"
    )

    plans = ExperiencePlanningSkill().run(
        group_context=context,
        conflicts=conflicts,
        negotiation_strategies=strategies,
    )
    role_ids = {role.role_id for role in context.roles}

    assert {plan.plan_type for plan in plans} == {"plan_a", "plan_b", "plan_c"}
    assert all(2 <= len(plan.stages) <= 4 for plan in plans)
    assert all(stage.priority_role_id in role_ids for plan in plans for stage in plan.stages)
    balanced = next(plan for plan in plans if plan.plan_type == "plan_c")
    assert "不是简单平均分最高" in balanced.recommendation_reason


def test_experience_planning_friends_demo_stages_reference_roles() -> None:
    context, conflicts, strategies = _build_inputs(
        "周末2男2女想出去玩半天，想拍照但也别太折腾，预算别太高，最好有点氛围"
    )

    plans = ExperiencePlanningSkill().run(
        group_context=context,
        conflicts=conflicts,
        negotiation_strategies=strategies,
    )
    role_ids = {role.role_id for role in context.roles}

    assert len(plans) == 3
    assert all(2 <= len(plan.stages) <= 4 for plan in plans)
    assert all(stage.priority_role_id in role_ids for plan in plans for stage in plan.stages)
    balanced = next(plan for plan in plans if plan.plan_type == "plan_c")
    assert "fairness_score" in balanced.recommendation_reason


def _plan_text(plans) -> str:  # type: ignore[no-untyped-def]
    return " ".join(
        json.dumps(plan.model_dump(), ensure_ascii=False, default=str)
        for plan in plans
    )


def _selected_categories(plans) -> set[str]:  # type: ignore[no-untyped-def]
    return {
        stage.selected_poi.category
        for plan in plans
        for stage in plan.stages
        if stage.selected_poi is not None
    }


def test_experience_planning_couple_query_uses_date_templates() -> None:
    context, conflicts, strategies = _build_inputs(
        "我们想安排一次情侣约会，帮我看看最近适合去哪、怎么安排"
    )

    plans = ExperiencePlanningSkill().run(
        group_context=context,
        conflicts=conflicts,
        negotiation_strategies=strategies,
    )
    text = _plan_text(plans)

    assert context.group_type == "couple"
    assert len(plans) == 3
    assert any("约会" in plan.title or "约会" in plan.theme for plan in plans)
    assert "亲子" not in text
    assert "孩子" not in text
    assert "亲子空间" not in text


def test_experience_planning_solo_and_general_do_not_use_family_templates() -> None:
    for query, expected_group in [
        ("一个人周末想出去逛逛，安静一点", "solo"),
        ("周末想出去玩一下，轻松一点，你安排", "unknown"),
    ]:
        context, conflicts, strategies = _build_inputs(query)
        plans = ExperiencePlanningSkill().run(
            group_context=context,
            conflicts=conflicts,
            negotiation_strategies=strategies,
        )
        text = _plan_text(plans)

        assert context.group_type == expected_group
        assert "亲子" not in text
        assert "孩子" not in text
        assert "亲子空间" not in text


def test_experience_planning_single_purpose_dining_returns_one_plan() -> None:
    context, conflicts, strategies = _build_inputs(
        "今晚只想吃个火锅，别安排别的，环境舒服点就行"
    )

    plans = ExperiencePlanningSkill().run(
        group_context=context,
        conflicts=conflicts,
        negotiation_strategies=strategies,
    )

    assert len(plans) == 1
    assert len(plans[0].stages) == 1
    assert plans[0].stages[0].stage_type == "dine"
    assert "一个最合适的推荐" in plans[0].recommendation_reason


def test_experience_planning_single_purpose_exhibition_returns_one_stage() -> None:
    context, conflicts, strategies = _build_inputs("今晚想跟朋友去看展")

    plans = ExperiencePlanningSkill().run(
        group_context=context,
        conflicts=conflicts,
        negotiation_strategies=strategies,
    )

    assert len(plans) == 1
    assert len(plans[0].stages) == 1
    assert plans[0].stages[0].stage_type == "explore"
    assert plans[0].stages[0].constraints["categories"] == ["展览"]


class _FakePromptRunner:
    def run(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        return PlanCandidateListOutput(
            items=[
                PlanCandidate(
                    plan_id="plan_b",
                    plan_type=PlanType.PLAN_B,
                    title="LLM 多段看展方案",
                    theme="看展后继续安排",
                    stages=[
                        Stage(
                            stage_id="stage_1",
                            stage_type=StageType.EXPLORE,
                            name="先看展",
                            experience_goal="看展",
                            duration_minutes=90,
                        ),
                        Stage(
                            stage_id="stage_2",
                            stage_type=StageType.DINE,
                            name="再喝咖啡",
                            experience_goal="聊天",
                            duration_minutes=45,
                        ),
                    ],
                )
            ]
        )


def test_experience_planning_collapses_llm_single_purpose_output() -> None:
    context, conflicts, strategies = _build_inputs("今晚想跟朋友去看展")

    plans = ExperiencePlanningSkill(prompt_runner=_FakePromptRunner()).run(
        group_context=context,
        conflicts=conflicts,
        negotiation_strategies=strategies,
    )

    assert len(plans) == 1
    assert plans[0].plan_id == "plan_a"
    assert len(plans[0].stages) == 1
    assert plans[0].stages[0].constraints["categories"] == ["展览"]
