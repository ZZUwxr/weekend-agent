from collections.abc import Callable
from typing import Any

from local_explorer_agent.app.domain.models import POI, GroupContext, PlanCandidate
from local_explorer_agent.app.domain.schemas import PlanPreviewStreamEvent
from local_explorer_agent.app.tools.base import ToolResult
from local_explorer_agent.app.tools.poi_query_tool import POIQueryRewriteTool
from local_explorer_agent.app.tools.poi_tool import POITool
from local_explorer_agent.app.tools.queue_tool import QueueTool
from local_explorer_agent.app.tools.weather_tool import WeatherTool

PlanPreviewEventCallback = Callable[[PlanPreviewStreamEvent], None]

# User intent keyword → POI categories to enforce
_INTENT_CATEGORY_MAP: dict[str, list[str]] = {
    "烧烤": ["烧烤"],
    "火锅": ["火锅"],
    "烤肉": ["烤肉", "烧烤"],
    "游乐园": ["游乐园"],
    "游乐场": ["游乐园"],
    "密室逃脱": ["密室逃脱"],
    "密室": ["密室逃脱"],
    "桌游": ["桌游"],
    "小剧场": ["小剧场"],
    "脱口秀": ["小剧场"],
    "黑盒剧场": ["小剧场"],
    "亲子空间": ["亲子空间"],
    "展览": ["展览"],
    "看展": ["展览"],
    "逛展": ["展览"],
    "拍照": ["展览"],
    "打卡": ["展览"],
    "出片": ["展览"],
    "好看": ["展览"],
    "氛围": ["展览"],
    "文艺": ["展览"],
    "网红点": ["展览", "咖啡", "书店"],
    "仪式感": ["展览", "甜品", "咖啡"],
    "甜品": ["甜品"],
    "蛋糕": ["甜品"],
    "冰淇淋": ["甜品"],
    "轻食": ["轻食"],
    "低卡": ["轻食"],
    "清淡": ["轻食"],
    "健身": ["轻食"],
    "书店": ["书店"],
    "咖啡": ["咖啡"],
    "茶馆": ["茶馆"],
    "喝茶": ["茶馆"],
    "夜间": ["夜间活动", "烧烤", "茶馆", "咖啡"],
    "下班后": ["夜间活动", "烧烤", "茶馆", "咖啡"],
    "烟火气": ["烧烤", "夜间活动"],
    "热闹": ["烧烤", "夜间活动", "茶馆", "咖啡"],
    "音乐": ["烧烤", "夜间活动"],
    "聚会": ["烧烤", "夜间活动", "茶馆", "咖啡"],
    "随便走走": ["Citywalk", "公园"],
    "街区": ["Citywalk", "买手店", "咖啡"],
    "小店": ["买手店", "咖啡"],
    "低预算": ["Citywalk", "公园", "咖啡"],
    "有意思": ["展览", "桌游"],
    "玩点": ["展览", "桌游"],
    "餐厅": ["餐厅"],
    "吃饭": ["餐厅"],
    "吃点": ["餐厅"],
    "孩子": ["亲子空间", "游乐园"],
    "女儿": ["亲子空间", "游乐园"],
    "儿子": ["亲子空间", "游乐园"],
}

_DINING_CATEGORIES = {"餐厅", "轻食", "火锅", "烧烤", "烤肉", "甜品", "茶馆", "咖啡", "桑拿鸡"}
_RELAX_CATEGORIES = {"咖啡", "茶馆", "书店", "公园", "Citywalk", "甜品", "夜间活动"}
_ACTIVITY_CATEGORIES = {
    "展览",
    "桌游",
    "密室逃脱",
    "小剧场",
    "游乐园",
    "亲子空间",
    "公园",
    "Citywalk",
    "买手店",
    "手作体验",
    "电竞馆",
    "洗浴汗蒸",
}
_STAGE_FALLBACK_CATEGORIES = {
    "dine": ["餐厅", "轻食", "咖啡", "茶馆", "甜品"],
    "energy_release": ["亲子空间", "游乐园", "公园"],
    "explore": ["展览", "书店", "公园", "咖啡", "Citywalk"],
    "relax": ["咖啡", "茶馆", "书店", "公园"],
}


class PlaceSelectionSkill:
    name = "place_selection"

    def __init__(
        self,
        *,
        poi_query_tool: POIQueryRewriteTool,
        poi_tool: POITool,
        queue_tool: QueueTool,
        weather_tool: WeatherTool,
    ) -> None:
        self.poi_query_tool = poi_query_tool
        self.poi_tool = poi_tool
        self.queue_tool = queue_tool
        self.weather_tool = weather_tool

    def run(
        self,
        *,
        candidate: PlanCandidate,
        group_context: GroupContext,
        city: str,
        event_callback: PlanPreviewEventCallback | None = None,
    ) -> PlanCandidate:
        intent_categories = _extract_intent_categories(group_context.input_query)
        weather_result = self.weather_tool.get_weather(city)
        self._emit_tool_call(
            event_callback,
            tool="weather",
            action="get_weather",
            params={"city": city},
            result=weather_result,
        )
        weather = weather_result.data or {}
        used_poi_ids: set[str] = set()
        for stage in candidate.stages:
            constraints = stage.constraints
            query_result = self.poi_query_tool.rewrite_stage_query(
                city=city,
                stage_type=str(stage.stage_type),
                stage_name=stage.name,
                experience_goal=stage.experience_goal,
                constraints=constraints,
            )
            self._emit_tool_call(
                event_callback,
                tool="poi_query",
                action="rewrite_stage_query",
                params={
                    "city": city,
                    "stage_id": stage.stage_id,
                    "stage_type": stage.stage_type,
                    "constraints": constraints,
                },
                result=query_result,
            )
            rewritten_query = query_result.data if isinstance(query_result.data, dict) else {}
            tags = _list_strings(
                rewritten_query.get("tags") or constraints.get("tags") or constraints.get("标签")
            )
            categories = _list_strings(
                rewritten_query.get("categories") or constraints.get("categories")
            )
            stage_type = str(stage.stage_type)
            priority_categories = _intent_categories_for_stage(stage_type, intent_categories)
            categories = _apply_stage_category_policy(
                stage_type=stage_type,
                categories=categories,
                priority_categories=priority_categories,
            )
            indoor = rewritten_query.get("indoor")
            indoor_filter = indoor if isinstance(indoor, bool) else constraints.get("indoor")
            max_queue_risk = rewritten_query.get("max_queue_risk")
            if priority_categories:
                max_queue_filter = None
            elif isinstance(max_queue_risk, str):
                max_queue_filter = str(max_queue_risk)
            elif constraints.get("avoid_queue"):
                max_queue_filter = "low"
            else:
                max_queue_filter = None
            # Fetch more candidates when user has explicit intent so
            # intent-matched POIs aren't cut by queue_risk sorting.
            search_limit = 12 if priority_categories else 6
            search_params = {
                "city": city,
                "tags": tags,
                "categories": categories,
                "indoor": indoor_filter,
                "max_queue_risk": max_queue_filter,
                "limit": search_limit,
                "stage_id": stage.stage_id,
            }
            result = self.poi_tool.search_poi(
                city=city,
                tags=tags,
                categories=categories,
                indoor=indoor_filter if isinstance(indoor_filter, bool) else None,
                max_queue_risk=max_queue_filter,
                limit=search_limit,
                priority_categories=priority_categories or None,
            )
            self._emit_tool_call(
                event_callback,
                tool="poi",
                action="search_poi",
                params=search_params,
                result=result,
            )
            pois: list[POI] = list(result.data or [])
            pois = _filter_stage_pois(stage_type, pois, priority_categories)
            if not pois and isinstance(indoor_filter, bool):
                retry = self.poi_tool.search_poi(
                    city=city,
                    tags=tags,
                    categories=categories,
                    indoor=None,
                    max_queue_risk=max_queue_filter,
                    limit=search_limit,
                    priority_categories=priority_categories or None,
                )
                self._emit_tool_call(
                    event_callback,
                    tool="poi",
                    action="search_poi",
                    params={**search_params, "indoor": None, "retry_without_indoor": True},
                    result=retry,
                )
                pois = _filter_stage_pois(stage_type, list(retry.data or []), priority_categories)
            if not pois:
                fallback_categories = _fallback_categories_for_stage(stage_type)
                fallback = self.poi_tool.search_poi(
                    city=city,
                    categories=fallback_categories,
                    limit=search_limit,
                    priority_categories=priority_categories or fallback_categories,
                )
                self._emit_tool_call(
                    event_callback,
                    tool="poi",
                    action="search_poi",
                    params={
                        "city": city,
                        "limit": search_limit,
                        "stage_id": stage.stage_id,
                        "categories": fallback_categories,
                        "fallback": True,
                    },
                    result=fallback,
                )
                pois = _filter_stage_pois(
                    stage_type,
                    list(fallback.data or []),
                    priority_categories,
                )

            if weather.get("outdoor_fit") is False:
                pois.sort(key=lambda poi: (not poi.indoor, poi.queue_risk != "low"))

            pois.sort(key=lambda poi: self._poi_rank(poi, constraints, tags, priority_categories))
            selected = next((poi for poi in pois if poi.id not in used_poi_ids), None)
            selected = selected or (pois[0] if pois else None)
            if selected:
                queue_result = self.queue_tool.get_queue_status(selected.id)
                self._emit_tool_call(
                    event_callback,
                    tool="queue",
                    action="get_queue_status",
                    params={"poi_id": selected.id, "stage_id": stage.stage_id},
                    result=queue_result,
                )
                queue_status = queue_result.data
                if queue_status and queue_status.get("risk") == "high" and len(pois) > 1:
                    selected = self._choose_queue_fallback(
                        pois=pois,
                        selected=selected,
                        intent_categories=priority_categories,
                    )
                used_poi_ids.add(selected.id)
            stage.selected_poi = selected
            stage.fallback_pois = [
                poi
                for poi in pois
                if (selected is None or poi.id != selected.id) and poi.id not in used_poi_ids
            ][:2]
        return candidate

    def _poi_rank(
        self,
        poi: POI,
        constraints: dict[str, object],
        rewritten_tags: list[str] | None,
        intent_categories: list[str] | None = None,
    ) -> tuple[int, int, int, int, int]:
        tags = set(rewritten_tags or constraints.get("tags") or constraints.get("标签") or [])
        poi_tags = set(
            poi.activity_tags + poi.mood_tags + poi.suitable_for + poi.conflict_relief_tags
        )
        risk_rank = {"low": 0, "medium": 1, "high": 2}
        # Preserve explicit intent order, e.g. 游乐园 should outrank later
        # child-safe fallbacks such as 亲子空间.
        intent_rank = {
            category: index for index, category in enumerate(intent_categories or [])
        }
        category_match = intent_rank.get(poi.category, len(intent_rank))
        return (
            category_match,
            -len(tags.intersection(poi_tags)),
            risk_rank.get(poi.queue_risk, 1),
            poi.energy_level,
            poi.avg_price or 0,
        )

    def _choose_queue_fallback(
        self,
        *,
        pois: list[POI],
        selected: POI,
        intent_categories: list[str],
    ) -> POI:
        if selected.category in intent_categories:
            intent_rank = {
                category: index for index, category in enumerate(intent_categories or [])
            }
            selected_rank = intent_rank.get(selected.category, len(intent_rank))
            intent_fallback = next(
                (
                    poi
                    for poi in pois[1:]
                    if intent_rank.get(poi.category) == selected_rank
                    and poi.queue_risk != "high"
                ),
                None,
            )
            return intent_fallback or selected
        return pois[1]

    def _emit_tool_call(
        self,
        event_callback: PlanPreviewEventCallback | None,
        *,
        tool: str,
        action: str,
        params: dict[str, Any],
        result: ToolResult,
    ) -> None:
        if event_callback is None:
            return
        event_callback(
            PlanPreviewStreamEvent(
                event="tool_call",
                data={
                    "step": 5,
                    "tool": tool,
                    "action": action,
                    "params": params,
                    "result": self._summarize_tool_result(result),
                },
            )
        )

    def _summarize_tool_result(self, result: ToolResult) -> dict[str, Any]:
        summary: dict[str, Any] = {
            "success": result.success,
            "latency_ms": result.latency_ms,
            "mock_scenario": result.mock_scenario,
        }
        if result.error_code:
            summary["error_code"] = result.error_code
        if result.error_message:
            summary["error_message"] = result.error_message

        data = result.data
        if isinstance(data, list):
            summary["count"] = len(data)
            if data and isinstance(data[0], POI):
                summary["poi_ids"] = [poi.id for poi in data[:4]]
                summary["poi_names"] = [poi.name for poi in data[:4]]
        elif isinstance(data, dict):
            for key in [
                "categories",
                "tags",
                "raw_categories",
                "raw_tags",
                "matched_rules",
                "condition",
                "temperature",
                "outdoor_fit",
                "rain_probability",
                "risk",
                "queue_minutes",
            ]:
                if key in data:
                    summary[key] = data[key]
        return summary


def _list_strings(value: object) -> list[str] | None:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return [stripped] if stripped else None
    if isinstance(value, list):
        values = [item.strip() for item in value if isinstance(item, str) and item.strip()]
        return values or None
    return None


def _extract_intent_categories(query: str) -> list[str]:
    """Extract POI categories from user query based on intent keywords."""
    categories: list[str] = []
    for keyword, cats in _INTENT_CATEGORY_MAP.items():
        if keyword in query:
            categories.extend(cats)
    return _dedupe(categories)


def _intent_categories_for_stage(stage_type: str, intent_categories: list[str]) -> list[str]:
    if stage_type == "dine":
        return [category for category in intent_categories if category in _DINING_CATEGORIES]
    if stage_type in {"energy_release", "explore"}:
        activity = [category for category in intent_categories if category in _ACTIVITY_CATEGORIES]
        if activity:
            return activity
        return [category for category in intent_categories if category not in _DINING_CATEGORIES]
    if stage_type == "relax":
        return [category for category in intent_categories if category in _RELAX_CATEGORIES]
    return []


def _apply_stage_category_policy(
    *,
    stage_type: str,
    categories: list[str] | None,
    priority_categories: list[str],
) -> list[str]:
    base = _dedupe(categories or [])
    if stage_type == "dine":
        allowed = _DINING_CATEGORIES
    elif stage_type == "energy_release":
        allowed = _ACTIVITY_CATEGORIES
    elif stage_type == "explore":
        allowed = _ACTIVITY_CATEGORIES.union(_RELAX_CATEGORIES)
    elif stage_type == "relax":
        allowed = _RELAX_CATEGORIES
    else:
        allowed = set(base)

    prioritized = [category for category in priority_categories if category in allowed]
    filtered = [category for category in base if category in allowed]
    if prioritized:
        return _dedupe(prioritized + filtered)
    if filtered:
        return filtered
    return _fallback_categories_for_stage(stage_type)


def _filter_stage_pois(
    stage_type: str,
    pois: list[POI],
    priority_categories: list[str],
) -> list[POI]:
    if not pois:
        return []
    priority_matches = [poi for poi in pois if poi.category in priority_categories]
    if priority_matches:
        return priority_matches
    if stage_type == "dine":
        dining = [poi for poi in pois if poi.category in _DINING_CATEGORIES]
        return dining or pois
    return pois


def _fallback_categories_for_stage(stage_type: str) -> list[str]:
    return list(_STAGE_FALLBACK_CATEGORIES.get(stage_type, []))


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
