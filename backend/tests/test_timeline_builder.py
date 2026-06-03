from datetime import datetime

from local_explorer_agent.app.agent.skills.timeline_builder import TimelineBuilderSkill
from local_explorer_agent.app.domain.enums import PlanType, StageType, TimelineItemType
from local_explorer_agent.app.domain.models import POI, PlanCandidate, Stage, TimelineItem
from local_explorer_agent.app.mobile.presenter import _build_timeline_segments


def _poi(poi_id: str, name: str) -> POI:
    return POI(
        id=poi_id,
        name=name,
        category="公园",
        city="深圳",
        lon=114.0,
        lat=22.5,
    )


def test_timeline_builder_prefers_taxi_minutes_over_long_walking_estimate() -> None:
    first = _poi("poi_a", "第一站")
    second = _poi("poi_b", "第二站")
    candidate = PlanCandidate(
        plan_id="plan_b",
        plan_type=PlanType.PLAN_B,
        title="远距离方案",
        theme="避免过长转场",
        stages=[
            Stage(
                stage_id="stage_a",
                stage_type=StageType.EXPLORE,
                name="第一站",
                experience_goal="轻松游玩",
                duration_minutes=60,
                selected_poi=first,
            ),
            Stage(
                stage_id="stage_b",
                stage_type=StageType.DINE,
                name="第二站",
                experience_goal="补充体力",
                duration_minutes=45,
                selected_poi=second,
            ),
        ],
        route_segments=[
            {
                "from": "poi_a",
                "to": "poi_b",
                "distance_meters": 45_120,
                "walking_minutes": 564,
                "taxi_minutes": 24,
                "route_note": "经纬度估算路线。",
            }
        ],
    )

    result = TimelineBuilderSkill().run(
        candidate=candidate,
        start_time=datetime.fromisoformat("2026-05-11T14:30:00"),
        duration_minutes=240,
    )

    transport = [
        item for item in result.timeline if item.type == TimelineItemType.TRANSPORT
    ][0]
    assert transport.mode == "taxi"
    assert transport.duration_minutes == 24
    assert transport.time == "15:40"
    assert all("9 小时" not in item.notes for item in result.timeline)


def test_mobile_presenter_repairs_persisted_long_transport_segments() -> None:
    first = _poi("poi_a", "第一站")
    second = _poi("poi_b", "第二站")
    candidate = PlanCandidate(
        plan_id="plan_b",
        plan_type=PlanType.PLAN_B,
        title="旧会话方案",
        theme="旧数据修正",
        stages=[
            Stage(
                stage_id="stage_a",
                stage_type=StageType.EXPLORE,
                name="第一站",
                experience_goal="轻松游玩",
                duration_minutes=60,
                selected_poi=first,
            ),
            Stage(
                stage_id="stage_b",
                stage_type=StageType.DINE,
                name="第二站",
                experience_goal="补充体力",
                duration_minutes=45,
                selected_poi=second,
            ),
        ],
        timeline=[
            TimelineItem(
                time="14:30",
                type=TimelineItemType.ACTIVITY,
                poi_id="poi_a",
                poi_name="第一站",
                duration_minutes=60,
                notes="轻松游玩",
            ),
            TimelineItem(
                time="15:30",
                type=TimelineItemType.TRANSPORT,
                poi_id="poi_b",
                poi_name="第二站",
                mode="taxi",
                duration_minutes=564,
                estimated_cost=24,
                notes="旧版保存了错误的步行时长。",
            ),
            TimelineItem(
                time="00:54",
                type=TimelineItemType.DINING,
                poi_id="poi_b",
                poi_name="第二站",
                duration_minutes=45,
                notes="补充体力",
            ),
        ],
        route_segments=[
            {
                "from": "poi_a",
                "to": "poi_b",
                "walking_minutes": 564,
                "taxi_minutes": 24,
            }
        ],
    )

    segments = _build_timeline_segments(candidate)

    assert segments[1].schedule_label == "15:30"
    assert segments[1].schedule_note == "24 分钟"
    assert segments[2].schedule_label == "15:54"
