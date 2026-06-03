from datetime import datetime

from local_explorer_agent.app.agent.skills.user_understanding import UserUnderstandingSkill
from local_explorer_agent.app.domain.memory import UserMemoryCompanion, UserMemoryContext


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


def test_user_understanding_couple_query_is_not_family() -> None:
    skill = UserUnderstandingSkill()

    context = skill.run(
        user_query="我们想安排一次情侣约会，帮我看看最近适合去哪、怎么安排",
        user_id="u003",
        city="深圳",
        start_time=datetime.fromisoformat("2026-05-11T18:00:00"),
        duration_minutes=240,
    )

    role_types = {role.role_type for role in context.roles}
    assert context.group_type == "couple"
    assert context.scene_label == "couple_date"
    assert {"user", "spouse"}.issubset(role_types)
    assert "child" not in role_types
    assert "亲子" not in " ".join(context.inferred_constraints)


def test_user_understanding_explicit_couple_ignores_child_memory() -> None:
    skill = UserUnderstandingSkill()
    memory = UserMemoryContext(
        user_id="u004",
        companions=[
            UserMemoryCompanion(
                companion_id="child_memory",
                display_name="孩子",
                role_type="child",
                age=5,
                soft_preferences=["亲子空间"],
            )
        ],
    )

    context = skill.run(
        user_query="今天晚上想和女朋友约会，找个有氛围的地方聊聊天",
        user_id="u004",
        city="深圳",
        start_time=datetime.fromisoformat("2026-05-11T18:00:00"),
        duration_minutes=180,
        user_memory=memory,
    )

    assert context.group_type == "couple"
    assert all(role.role_type != "child" for role in context.roles)


def test_user_understanding_solo_and_general_do_not_default_to_family() -> None:
    skill = UserUnderstandingSkill()

    solo = skill.run(
        user_query="一个人周末想出去逛逛，安静一点",
        user_id="u005",
        city="深圳",
        start_time=datetime.fromisoformat("2026-05-11T14:00:00"),
        duration_minutes=180,
    )
    general = skill.run(
        user_query="周末想出去玩一下，轻松一点，你安排",
        user_id="u006",
        city="深圳",
        start_time=datetime.fromisoformat("2026-05-11T14:00:00"),
        duration_minutes=180,
    )

    assert solo.group_type == "solo"
    assert general.group_type == "unknown"
    assert all(role.role_type != "child" for role in [*solo.roles, *general.roles])


def test_user_understanding_empty_memory_does_not_turn_general_into_solo() -> None:
    skill = UserUnderstandingSkill()

    context = skill.run(
        user_query="周末想出去玩一下，轻松一点，你安排",
        user_id="u007",
        city="深圳",
        start_time=datetime.fromisoformat("2026-05-11T14:00:00"),
        duration_minutes=180,
        user_memory=UserMemoryContext(user_id="u007"),
    )

    assert context.group_type == "unknown"
    assert context.scene_label == "general_local_outing"
