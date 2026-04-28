from datetime import datetime, timedelta

from local_explorer_agent.app.domain.enums import StageType, TimelineItemType
from local_explorer_agent.app.domain.models import PlanCandidate, TimelineItem


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
                transport_minutes = int(
                    route.get("walking_minutes") or route.get("taxi_minutes") or 10
                )
                mode = "walk" if transport_minutes <= 15 else "taxi"
                timeline.append(
                    TimelineItem(
                        time=current.strftime("%H:%M"),
                        type=TimelineItemType.TRANSPORT,
                        poi_id=poi.id,
                        poi_name=poi.name,
                        mode=mode,
                        duration_minutes=transport_minutes,
                        estimated_cost=0 if mode == "walk" else 24,
                        notes=str(route.get("route_note", "短距离转场")),
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
                        notes="给亲子节奏、洗手间和临时调整预留缓冲。",
                    )
                )
                current += timedelta(minutes=10)

        candidate.timeline = timeline
        return candidate
