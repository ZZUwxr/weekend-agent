from local_explorer_agent.app.domain.models import POI, GroupContext, PlanCandidate
from local_explorer_agent.app.tools.poi_tool import POITool
from local_explorer_agent.app.tools.queue_tool import QueueTool
from local_explorer_agent.app.tools.weather_tool import WeatherTool


class PlaceSelectionSkill:
    name = "place_selection"

    def __init__(
        self,
        *,
        poi_tool: POITool,
        queue_tool: QueueTool,
        weather_tool: WeatherTool,
    ) -> None:
        self.poi_tool = poi_tool
        self.queue_tool = queue_tool
        self.weather_tool = weather_tool

    def run(
        self,
        *,
        candidate: PlanCandidate,
        group_context: GroupContext,
        city: str,
    ) -> PlanCandidate:
        del group_context
        weather = self.weather_tool.get_weather(city).data or {}
        for stage in candidate.stages:
            constraints = stage.constraints
            tags = constraints.get("tags") or constraints.get("标签")
            result = self.poi_tool.search_poi(
                city=city,
                tags=tags,
                categories=constraints.get("categories"),
                indoor=constraints.get("indoor"),
                max_queue_risk="low" if constraints.get("avoid_queue") else None,
                limit=4,
            )
            pois: list[POI] = list(result.data or [])
            if not pois:
                fallback = self.poi_tool.search_poi(city=city, limit=4)
                pois = list(fallback.data or [])

            if weather.get("outdoor_fit") is False:
                pois.sort(key=lambda poi: (not poi.indoor, poi.queue_risk != "low"))

            pois.sort(key=lambda poi: self._poi_rank(poi, constraints))
            selected = pois[0] if pois else None
            if selected:
                queue_status = self.queue_tool.get_queue_status(selected.id).data
                if queue_status and queue_status.get("risk") == "high" and len(pois) > 1:
                    selected = pois[1]
            stage.selected_poi = selected
            stage.fallback_pois = [
                poi for poi in pois if selected is None or poi.id != selected.id
            ][:2]
        return candidate

    def _poi_rank(self, poi: POI, constraints: dict[str, object]) -> tuple[int, int, int, int]:
        tags = set(constraints.get("tags") or constraints.get("标签") or [])
        poi_tags = set(
            poi.activity_tags + poi.mood_tags + poi.suitable_for + poi.conflict_relief_tags
        )
        risk_rank = {"low": 0, "medium": 1, "high": 2}
        return (
            -len(tags.intersection(poi_tags)),
            risk_rank.get(poi.queue_risk, 1),
            poi.energy_level,
            poi.avg_price or 0,
        )
