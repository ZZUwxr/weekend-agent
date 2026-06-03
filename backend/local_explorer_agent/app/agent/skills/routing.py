from collections.abc import Callable
from typing import Any

from local_explorer_agent.app.domain.models import PlanCandidate
from local_explorer_agent.app.domain.schemas import PlanPreviewStreamEvent
from local_explorer_agent.app.tools.base import ToolResult
from local_explorer_agent.app.tools.route_tool import RouteTool

PlanPreviewEventCallback = Callable[[PlanPreviewStreamEvent], None]


class RoutingSkill:
    name = "routing"

    def __init__(self, route_tool: RouteTool) -> None:
        self.route_tool = route_tool

    def run(
        self,
        candidate: PlanCandidate,
        event_callback: PlanPreviewEventCallback | None = None,
    ) -> PlanCandidate:
        route_segments: list[dict[str, object]] = []
        selected_pois = [stage.selected_poi for stage in candidate.stages if stage.selected_poi]
        for current, nxt in zip(selected_pois, selected_pois[1:], strict=False):
            result = self.route_tool.get_route(current.id, nxt.id)
            self._emit_tool_call(
                event_callback,
                params={
                    "from_poi_id": current.id,
                    "to_poi_id": nxt.id,
                    "candidate_id": candidate.plan_id,
                },
                result=result,
            )
            if result.success and result.data:
                route_segments.append(result.data)
        candidate.route_segments = route_segments
        return candidate

    def _emit_tool_call(
        self,
        event_callback: PlanPreviewEventCallback | None,
        *,
        params: dict[str, Any],
        result: ToolResult,
    ) -> None:
        if event_callback is None:
            return
        event_callback(
            PlanPreviewStreamEvent(
                event="tool_call",
                data={
                    "step": 6,
                    "tool": "route",
                    "action": "get_route",
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
        if isinstance(result.data, dict):
            for key in [
                "from",
                "to",
                "distance_meters",
                "walking_minutes",
                "taxi_minutes",
                "route_type",
                "energy_cost",
            ]:
                if key in result.data:
                    summary[key] = result.data[key]
        return summary
