from datetime import datetime

from local_explorer_agent.app.agent.skills.user_understanding import UserUnderstandingSkill


def test_user_understanding_family_query() -> None:
    skill = UserUnderstandingSkill()

    context = skill.run(
        user_query="今天下午想和老婆孩子出去玩几小时，别太远，老婆最近在减肥，孩子5岁",
        user_id="u001",
        city="深圳",
        start_time=datetime.fromisoformat("2026-05-10T14:00:00"),
        duration_minutes=240,
    )

    role_types = {role.role_type for role in context.roles}
    role_ids = {role.role_id for role in context.roles}
    assert context.group_type == "family"
    assert {"user", "spouse", "child"}.issubset(role_types)
    assert {"adult_user", "spouse_dieter", "child_5yo"}.issubset(role_ids)
    assert context.group_size == 3
    assert context.confidence_summary["overall"] >= 0.8
    assert any("距离不能太远" in item for item in context.inferred_constraints)


def test_user_understanding_friends_query() -> None:
    skill = UserUnderstandingSkill()

    context = skill.run(
        user_query="周末2男2女想出去玩半天，想拍照但也别太折腾，预算别太高，最好有点氛围",
        user_id="u002",
        city="深圳",
        start_time=datetime.fromisoformat("2026-05-11T14:00:00"),
        duration_minutes=240,
    )

    role_ids = {role.role_id for role in context.roles}
    assert context.group_type == "friends"
    assert context.group_size == 4
    assert {
        "photo_oriented_role",
        "practical_oriented_role",
        "budget_sensitive_role",
        "lively_oriented_role",
    }.issubset(role_ids)
