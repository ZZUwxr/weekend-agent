"""Fine-grained fact tools exposed to the ReAct runtime."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from local_explorer_agent.app.domain.models import POI
from local_explorer_agent.app.tools.base import ToolResult

if TYPE_CHECKING:
    from local_explorer_agent.app.agent.react.state import AgentState
    from local_explorer_agent.app.tools.poi_tool import POITool
    from local_explorer_agent.app.tools.queue_tool import QueueTool
    from local_explorer_agent.app.tools.route_tool import RouteTool
    from local_explorer_agent.app.tools.weather_tool import WeatherTool


class POISearchArgs(BaseModel):
    city: str
    query: str | None = None
    categories: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    suitable_for: list[str] = Field(default_factory=list)
    indoor: bool | None = None
    max_distance_km: float | None = None
    max_results: int = Field(default=10, ge=1, le=20)
    max_price: int | None = None
    max_energy_level: int | None = Field(default=None, ge=0, le=5)
    low_queue_only: bool = False


class POIDetailArgs(BaseModel):
    poi_id: str


class RouteSearchArgs(BaseModel):
    from_poi_id: str | None = None
    to_poi_id: str | None = None
    from_location: dict[str, float] | None = None
    to_location: dict[str, float] | None = None
    mode: str | None = None


class WeatherLookupArgs(BaseModel):
    city: str
    start_time: str | None = None
    duration_minutes: int | None = Field(default=None, gt=0, le=720)


class QueueLookupArgs(BaseModel):
    poi_id: str


class POISearchTool:
    name = "poi_search"
    description = "按城市、类别、标签、人群、室内、价格、体力、排队和距离搜索 POI 摘要"
    args_schema = POISearchArgs
    is_execution_tool = False
    requires_confirmation = False
    prepare_tool = False

    def __init__(self, poi_tool: POITool) -> None:
        self._poi_tool = poi_tool

    async def run(self, args: BaseModel, state: AgentState) -> ToolResult:
        assert isinstance(args, POISearchArgs)
        try:
            tags = _merge_terms(args.tags, args.query)
            max_queue_risk = "low" if args.low_queue_only else None
            result = self._poi_tool.search_poi(
                city=args.city,
                tags=tags,
                categories=args.categories or None,
                indoor=args.indoor,
                max_queue_risk=max_queue_risk,
                limit=max(args.max_results * 2, args.max_results),
                priority_categories=args.categories or None,
            )
            if not result.success:
                return result

            pois = [_coerce_poi(item) for item in result.data or []]
            pois = [poi for poi in pois if poi is not None]
            pois = _filter_pois(pois, args, state)
            summaries = [_poi_summary(poi, state) for poi in pois[: args.max_results]]
            return ToolResult(
                success=bool(summaries),
                data={
                    "city": args.city,
                    "count": len(summaries),
                    "pois": summaries,
                    "filters": _active_filters(args),
                },
                error_message=None if summaries else "No POI records matched the ReAct search",
                mock_scenario=result.mock_scenario,
            )
        except Exception as exc:  # noqa: BLE001
            return ToolResult(success=False, error_message=str(exc))


class POIDetailTool:
    name = "poi_detail"
    description = "根据 poi_id 获取 POI 详情摘要，用于确认营业时间、价格、人群适配和风险"
    args_schema = POIDetailArgs
    is_execution_tool = False
    requires_confirmation = False
    prepare_tool = False

    def __init__(self, poi_tool: POITool) -> None:
        self._poi_tool = poi_tool

    async def run(self, args: BaseModel, state: AgentState) -> ToolResult:
        assert isinstance(args, POIDetailArgs)
        try:
            result = self._poi_tool.get_poi_detail(args.poi_id)
            if not result.success:
                return result
            poi = _coerce_poi(result.data)
            if poi is None:
                return ToolResult(success=False, error_message=f"POI {args.poi_id} not found")
            return ToolResult(success=True, data={"poi": _poi_detail(poi, state)})
        except Exception as exc:  # noqa: BLE001
            return ToolResult(success=False, error_message=str(exc))


class RouteSearchTool:
    name = "route_search"
    description = "查询两个 POI 或两个经纬度之间的路线，缺少精确路线时返回距离估算 fallback"
    args_schema = RouteSearchArgs
    is_execution_tool = False
    requires_confirmation = False
    prepare_tool = False

    def __init__(self, route_tool: RouteTool, poi_tool: POITool) -> None:
        self._route_tool = route_tool
        self._poi_tool = poi_tool

    async def run(self, args: BaseModel, state: AgentState) -> ToolResult:
        assert isinstance(args, RouteSearchArgs)
        try:
            if args.from_poi_id and args.to_poi_id:
                result = self._route_tool.get_route(args.from_poi_id, args.to_poi_id)
                if not result.success:
                    return result
                route = dict(result.data or {})
                route.setdefault("mode", args.mode)
                route["fallback_used"] = result.mock_scenario == "distance_estimated"
                return ToolResult(success=True, data={"route": _route_summary(route)})

            from_location = args.from_location or _poi_location(self._poi_tool, args.from_poi_id)
            to_location = args.to_location or _poi_location(self._poi_tool, args.to_poi_id)
            if not from_location or not to_location:
                return ToolResult(
                    success=False,
                    error_message="route_search requires POI IDs or from/to locations",
                )
            route = _estimate_route(from_location, to_location, args.mode)
            return ToolResult(success=True, data={"route": route})
        except Exception as exc:  # noqa: BLE001
            return ToolResult(success=False, error_message=str(exc))


class WeatherLookupTool:
    name = "weather_lookup"
    description = "按城市和计划时间查询天气摘要、降雨/高温/户外风险"
    args_schema = WeatherLookupArgs
    is_execution_tool = False
    requires_confirmation = False
    prepare_tool = False

    def __init__(self, weather_tool: WeatherTool) -> None:
        self._weather_tool = weather_tool

    async def run(self, args: BaseModel, state: AgentState) -> ToolResult:
        assert isinstance(args, WeatherLookupArgs)
        try:
            result = self._weather_tool.get_weather(args.city)
            if not result.success:
                return result
            data = dict(result.data or {})
            temp = data.get("temperature")
            rain_probability = float(data.get("rain_probability", 0) or 0)
            outdoor_fit = bool(data.get("outdoor_fit", True))
            risk_flags = []
            if rain_probability >= 0.5:
                risk_flags.append("rain")
            if isinstance(temp, int | float) and temp >= 32:
                risk_flags.append("heat")
            if not outdoor_fit:
                risk_flags.append("outdoor_not_recommended")
            return ToolResult(
                success=True,
                data={
                    "city": data.get("city", args.city),
                    "condition": data.get("condition", "unknown"),
                    "temperature": temp,
                    "rain_probability": rain_probability,
                    "outdoor_fit": outdoor_fit,
                    "risk_flags": risk_flags,
                    "start_time": args.start_time,
                    "duration_minutes": args.duration_minutes,
                    "suggestion": data.get("suggestion"),
                },
                mock_scenario=result.mock_scenario,
            )
        except Exception as exc:  # noqa: BLE001
            return ToolResult(success=False, error_message=str(exc))


class QueueLookupTool:
    name = "queue_lookup"
    description = "根据 poi_id 查询排队分钟数和风险，用于热门、儿童同行或时间紧张场景"
    args_schema = QueueLookupArgs
    is_execution_tool = False
    requires_confirmation = False
    prepare_tool = False

    def __init__(self, queue_tool: QueueTool) -> None:
        self._queue_tool = queue_tool

    async def run(self, args: BaseModel, state: AgentState) -> ToolResult:
        assert isinstance(args, QueueLookupArgs)
        try:
            result = self._queue_tool.get_queue_status(args.poi_id)
            if not result.success:
                return result
            data = dict(result.data or {})
            return ToolResult(
                success=True,
                data={
                    "poi_id": data.get("poi_id", args.poi_id),
                    "queue_minutes": data.get("queue_minutes"),
                    "risk": data.get("risk", "medium"),
                    "warning": data.get("risk") == "high",
                },
                mock_scenario=result.mock_scenario,
            )
        except Exception as exc:  # noqa: BLE001
            return ToolResult(success=False, error_message=str(exc))


def _merge_terms(tags: list[str], query: str | None) -> list[str] | None:
    terms = [term for term in tags if term]
    if query:
        terms.append(query)
    return terms or None


def _coerce_poi(value: Any) -> POI | None:
    if isinstance(value, POI):
        return value
    if isinstance(value, dict):
        try:
            return POI.model_validate(value)
        except Exception:
            return None
    return None


def _filter_pois(
    pois: list[POI],
    args: POISearchArgs,
    state: AgentState,
) -> list[POI]:
    suitable_terms = set(args.suitable_for)
    if suitable_terms:
        pois = [poi for poi in pois if suitable_terms.intersection(set(poi.suitable_for))]
    if args.max_price is not None:
        pois = [poi for poi in pois if poi.avg_price is None or poi.avg_price <= args.max_price]
    if args.max_energy_level is not None:
        pois = [poi for poi in pois if poi.energy_level <= args.max_energy_level]
    if args.max_distance_km is not None and state.request.location is not None:
        origin = {"lat": state.request.location.lat, "lon": state.request.location.lon}
        pois = [
            poi for poi in pois
            if _distance_km(origin, {"lat": poi.lat, "lon": poi.lon}) <= args.max_distance_km
        ]
    return pois


def _active_filters(args: POISearchArgs) -> dict[str, Any]:
    return {
        "categories": args.categories,
        "tags": args.tags,
        "suitable_for": args.suitable_for,
        "indoor": args.indoor,
        "max_distance_km": args.max_distance_km,
        "max_price": args.max_price,
        "max_energy_level": args.max_energy_level,
        "low_queue_only": args.low_queue_only,
    }


def _poi_summary(poi: POI, state: AgentState) -> dict[str, Any]:
    summary = {
        "poi_id": poi.id,
        "name": poi.name,
        "category": poi.category,
        "area": poi.area,
        "indoor": poi.indoor,
        "queue_risk": poi.queue_risk,
        "energy_level": poi.energy_level,
        "avg_price": poi.avg_price,
        "suitable_for": poi.suitable_for[:5],
        "tags": (poi.activity_tags + poi.mood_tags)[:6],
    }
    if state.request.location is not None:
        origin = {"lat": state.request.location.lat, "lon": state.request.location.lon}
        summary["distance_km"] = round(
            _distance_km(origin, {"lat": poi.lat, "lon": poi.lon}),
            2,
        )
    return summary


def _poi_detail(poi: POI, state: AgentState) -> dict[str, Any]:
    detail = _poi_summary(poi, state)
    detail.update({
        "city": poi.city,
        "address": poi.address,
        "open_hours": poi.open_hours,
        "avg_stay_minutes": poi.avg_stay_minutes,
        "weather_fit": poi.weather_fit,
        "crowd_risk": poi.crowd_risk,
        "facilities": poi.facilities,
        "business_rules": poi.business_rules,
        "conflict_relief_tags": poi.conflict_relief_tags[:6],
    })
    return detail


def _poi_location(poi_tool: POITool, poi_id: str | None) -> dict[str, float] | None:
    if not poi_id:
        return None
    result = poi_tool.get_poi_detail(poi_id)
    if not result.success:
        return None
    poi = _coerce_poi(result.data)
    if poi is None:
        return None
    return {"lat": poi.lat, "lon": poi.lon}


def _route_summary(route: dict[str, Any]) -> dict[str, Any]:
    return {
        "from": route.get("from"),
        "to": route.get("to"),
        "distance_meters": route.get("distance_meters"),
        "walking_minutes": route.get("walking_minutes"),
        "taxi_minutes": route.get("taxi_minutes"),
        "transit_modes": route.get("transit_modes", []),
        "route_type": route.get("route_type"),
        "energy_cost": route.get("energy_cost"),
        "route_note": route.get("route_note"),
        "mode": route.get("mode"),
        "confidence": 0.65 if route.get("fallback_used") else 0.9,
        "fallback_used": bool(route.get("fallback_used")),
    }


def _estimate_route(
    from_location: dict[str, float],
    to_location: dict[str, float],
    mode: str | None,
) -> dict[str, Any]:
    meters = int(_distance_km(from_location, to_location) * 1000)
    walking_minutes = max(5, int(meters / 80))
    route = {
        "from": "from_location",
        "to": "to_location",
        "distance_meters": meters,
        "walking_minutes": walking_minutes,
        "taxi_minutes": max(6, int(meters / 350)),
        "transit_modes": ["walking", "taxi"],
        "route_type": "经纬度估算路线",
        "energy_cost": min(5, max(1, walking_minutes // 10)),
        "route_note": "没有精确路线边，使用经纬度距离估算。",
        "mode": mode,
        "confidence": 0.55,
        "fallback_used": True,
    }
    return route


def _distance_km(left: dict[str, float], right: dict[str, float]) -> float:
    lat1, lon1 = float(left["lat"]), float(left["lon"])
    lat2, lon2 = float(right["lat"]), float(right["lon"])
    radius_km = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return radius_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
