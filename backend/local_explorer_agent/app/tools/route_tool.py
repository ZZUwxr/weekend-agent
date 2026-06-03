import math
import time

from local_explorer_agent.app.domain.models import POI
from local_explorer_agent.app.repositories.poi_repository import POIRepository
from local_explorer_agent.app.repositories.route_repository import RouteRepository
from local_explorer_agent.app.tools.base import BaseTool, ToolResult


class RouteTool(BaseTool):
    name = "route_tool"

    def __init__(self, route_repository: RouteRepository, poi_repository: POIRepository) -> None:
        self.route_repository = route_repository
        self.poi_repository = poi_repository

    def get_route(self, from_poi_id: str, to_poi_id: str) -> ToolResult:
        started_at = time.perf_counter()
        route = self.route_repository.get_route(from_poi_id, to_poi_id)
        if route:
            return self._result(data=route, started_at=started_at)

        from_poi = self.poi_repository.get(from_poi_id)
        to_poi = self.poi_repository.get(to_poi_id)
        if not from_poi or not to_poi:
            return self._result(
                success=False,
                error_code="route_not_found",
                error_message="Missing POI detail for route fallback",
                started_at=started_at,
            )
        return self._result(
            data=self._estimate_route(from_poi, to_poi),
            started_at=started_at,
            mock_scenario="distance_estimated",
        )

    def _estimate_route(self, from_poi: POI, to_poi: POI) -> dict[str, object]:
        meters = int(_haversine_meters(from_poi.lat, from_poi.lon, to_poi.lat, to_poi.lon))
        walking_minutes = max(5, int(meters / 80))
        return {
            "from": from_poi.id,
            "to": to_poi.id,
            "distance_meters": meters,
            "walking_minutes": walking_minutes,
            "taxi_minutes": max(6, int(meters / 350)),
            "transit_modes": ["walking", "taxi"],
            "route_type": "估算路线",
            "energy_cost": min(5, max(1, walking_minutes // 10)),
            "route_note": "本地路线边缺失，使用经纬度距离估算。",
        }


def _haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6_371_000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
