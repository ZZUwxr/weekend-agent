from datetime import datetime, timedelta

from local_explorer_agent.app.domain.enums import StageType, TimelineItemType
from local_explorer_agent.app.domain.models import PlanCandidate, TimelineItem


_MAX_WALKING_MINUTES = 15
_MAX_TAXI_MINUTES = 60
_DEFAULT_TRANSPORT_MINUTES = 10
_DEFAULT_TAXI_COST = 24


class TimelineBuilderSkill:
    name = "timeline_builder"

    def run(
        self,
        *,
        candidate: PlanCandidate,
        start_time: datetime,
        duration_minutes: int,
    ) -> PlanCandidate:
        del duration_minutes
        current = start_time
        timeline: list[TimelineItem] = []
        route_lookup = {
            (item.get("from"), item.get("to")): item for item in candidate.route_segments
        }

        previous_poi_id: str | None = None
        for stage in candidate.stages:
            poi = stage.selected_poi
            if previous_poi_id and poi:
                route = route_lookup.get((previous_poi_id, poi.id), {})
                mode, transport_minutes = select_route_transport(route)
                timeline.append(
                    TimelineItem(
                        time=current.strftime("%H:%M"),
                        type=TimelineItemType.TRANSPORT,
                        poi_id=poi.id,
                        poi_name=poi.name,
                        mode=mode,
                        duration_minutes=transport_minutes,
                        estimated_cost=0 if mode == "walk" else _route_cost(route),
                        notes=str(route.get("route_note", _default_route_note(mode))),
                    )
                )
                current += timedelta(minutes=transport_minutes)

            item_type = (
                TimelineItemType.DINING
                if stage.stage_type == StageType.DINE
                else TimelineItemType.ACTIVITY
            )
            timeline.append(
                TimelineItem(
                    time=current.strftime("%H:%M"),
                    type=item_type,
                    poi_id=poi.id if poi else None,
                    poi_name=poi.name if poi else stage.name,
                    duration_minutes=stage.duration_minutes,
                    estimated_cost=float(poi.avg_price or 0) if poi else 0,
                    notes=stage.experience_goal,
                )
            )
            current += timedelta(minutes=stage.duration_minutes)
            previous_poi_id = poi.id if poi else previous_poi_id

            if stage != candidate.stages[-1]:
                timeline.append(
                    TimelineItem(
                        time=current.strftime("%H:%M"),
                        type=TimelineItemType.BUFFER,
                        duration_minutes=10,
                        estimated_cost=0,
                        notes="给转场、洗手间和临时调整预留缓冲。",
                    )
                )
                current += timedelta(minutes=10)

        candidate.timeline = timeline
        return candidate


def select_route_transport(route: dict[str, object]) -> tuple[str, int]:
    walking_minutes = _positive_int(route.get("walking_minutes"))
    taxi_minutes = _positive_int(route.get("taxi_minutes"))
    duration_minutes = _positive_int(route.get("duration_minutes") or route.get("duration"))
    mode_hint = _route_mode_hint(route)

    if mode_hint == "taxi":
        return "taxi", _cap_taxi_minutes(taxi_minutes or duration_minutes or walking_minutes)

    if mode_hint == "walk" and walking_minutes and walking_minutes <= _MAX_WALKING_MINUTES:
        return "walk", walking_minutes

    if walking_minutes and walking_minutes <= _MAX_WALKING_MINUTES:
        return "walk", walking_minutes

    if taxi_minutes:
        return "taxi", _cap_taxi_minutes(taxi_minutes)

    if duration_minutes:
        if duration_minutes <= _MAX_WALKING_MINUTES:
            return "walk", duration_minutes
        return "taxi", _cap_taxi_minutes(duration_minutes)

    if walking_minutes:
        estimated_taxi = max(6, round(walking_minutes * 80 / 350))
        return "taxi", _cap_taxi_minutes(estimated_taxi)

    return "walk", _DEFAULT_TRANSPORT_MINUTES


def _route_mode_hint(route: dict[str, object]) -> str | None:
    for key in ("mode", "transport_mode", "recommended_mode", "route_type"):
        value = route.get(key)
        if value is None:
            continue
        text = str(value).lower()
        if any(token in text for token in ("taxi", "car", "drive", "打车", "驾车", "出租车", "网约车")):
            return "taxi"
        if any(token in text for token in ("walk", "步行")):
            return "walk"
    return None


def _positive_int(value: object) -> int | None:
    try:
        minutes = int(float(str(value)))
    except (TypeError, ValueError):
        return None
    return minutes if minutes > 0 else None


def _cap_taxi_minutes(minutes: int | None) -> int:
    if minutes is None:
        return _DEFAULT_TRANSPORT_MINUTES
    return min(minutes, _MAX_TAXI_MINUTES)


def _route_cost(route: dict[str, object]) -> float:
    for key in ("estimated_cost", "cost", "taxi_cost"):
        value = route.get(key)
        try:
            cost = float(str(value))
        except (TypeError, ValueError):
            continue
        if cost > 0:
            return cost
    return _DEFAULT_TAXI_COST


def _default_route_note(mode: str) -> str:
    return "建议打车转场，减少路上消耗。" if mode == "taxi" else "短距离步行转场。"
