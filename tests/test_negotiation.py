from datetime import datetime

from local_explorer_agent.app.agent.skills.conflict_detection import ConflictDetectionSkill
from local_explorer_agent.app.agent.skills.negotiation import NegotiationSkill
from local_explorer_agent.app.agent.skills.user_understanding import UserUnderstandingSkill


def test_negotiation_has_actionable_strategies() -> None:
    context = UserUnderstandingSkill().run(
        user_query="今天下午想和老婆孩子出去玩几小时，别太远，老婆最近在减肥，孩子5岁",
        user_id="u001",
        city="深圳",
        start_time=datetime.fromisoformat("2026-05-10T14:00:00"),
        duration_minutes=240,
    )
    conflicts = ConflictDetectionSkill().run(context)

    strategies = NegotiationSkill().run(group_context=context, conflicts=conflicts)
    strategy_types = {strategy.strategy_type for strategy in strategies}

    assert {"rotate_priority", "soften_conflict", "compensate_loser", "min_regret"}.issubset(
        strategy_types
    )
    assert all(strategy.stage_policy for strategy in strategies)
    assert all(strategy.compensation_policy for strategy in strategies)


def test_negotiation_friends_has_four_strategies() -> None:
    context = UserUnderstandingSkill().run(
        user_query="周末2男2女想出去玩半天，想拍照但也别太折腾，预算别太高，最好有点氛围",
        user_id="u002",
        city="深圳",
        start_time=datetime.fromisoformat("2026-05-11T14:00:00"),
        duration_minutes=240,
    )
    conflicts = ConflictDetectionSkill().run(context)

    strategies = NegotiationSkill().run(group_context=context, conflicts=conflicts)
    strategy_types = {strategy.strategy_type for strategy in strategies}

    assert {"rotate_priority", "soften_conflict", "compensate_loser", "min_regret"}.issubset(
        strategy_types
    )
    assert any(
        "photo_oriented_role" in policy_value
        for strategy in strategies
        for policy_value in strategy.stage_policy.values()
        if isinstance(policy_value, list)
    )
