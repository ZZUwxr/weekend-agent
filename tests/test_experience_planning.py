from datetime import datetime

from local_explorer_agent.app.agent.skills.conflict_detection import ConflictDetectionSkill
from local_explorer_agent.app.agent.skills.experience_planning import ExperiencePlanningSkill
from local_explorer_agent.app.agent.skills.negotiation import NegotiationSkill
from local_explorer_agent.app.agent.skills.user_understanding import UserUnderstandingSkill


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

    assert {plan.plan_type for plan in plans} == {"plan_a", "plan_b", "recommended"}
    assert all(2 <= len(plan.stages) <= 4 for plan in plans)
    assert all(stage.priority_role_id in role_ids for plan in plans for stage in plan.stages)
    recommended = next(plan for plan in plans if plan.plan_type == "recommended")
    assert "不是简单平均分最高" in recommended.recommendation_reason


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
    recommended = next(plan for plan in plans if plan.plan_type == "recommended")
    assert "fairness_score" in recommended.recommendation_reason
