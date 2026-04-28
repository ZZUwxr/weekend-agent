from datetime import datetime

from local_explorer_agent.app.agent.skills.conflict_detection import ConflictDetectionSkill
from local_explorer_agent.app.agent.skills.user_understanding import UserUnderstandingSkill


def test_conflict_detection_family_diet_and_energy() -> None:
    context = UserUnderstandingSkill().run(
        user_query="今天下午想和老婆孩子出去玩几小时，别太远，老婆最近在减肥，孩子5岁",
        user_id="u001",
        city="深圳",
        start_time=datetime.fromisoformat("2026-05-10T14:00:00"),
        duration_minutes=240,
    )

    conflicts = ConflictDetectionSkill().run(context)
    conflict_types = {conflict.conflict_type for conflict in conflicts}
    conflict_ids = {conflict.conflict_id for conflict in conflicts}

    assert "energy_mismatch" in conflict_types
    assert "diet_conflict" in conflict_types
    assert {"energy_mismatch", "diet_conflict", "participation_gap"}.issubset(conflict_ids)
    assert all(conflict.involved_roles for conflict in conflicts)
    assert all(conflict.affected_decisions for conflict in conflicts)


def test_conflict_detection_friends_demo() -> None:
    context = UserUnderstandingSkill().run(
        user_query="周末2男2女想出去玩半天，想拍照但也别太折腾，预算别太高，最好有点氛围",
        user_id="u002",
        city="深圳",
        start_time=datetime.fromisoformat("2026-05-11T14:00:00"),
        duration_minutes=240,
    )

    conflicts = ConflictDetectionSkill().run(context)
    conflict_ids = {conflict.conflict_id for conflict in conflicts}
    conflict_types = {conflict.conflict_type for conflict in conflicts}

    assert "atmosphere_vs_efficiency_conflict" in conflict_ids
    assert "quiet_vs_lively_conflict" in conflict_ids
    assert "photo_vs_practical" in conflict_types
    assert all(conflict.involved_roles for conflict in conflicts)
