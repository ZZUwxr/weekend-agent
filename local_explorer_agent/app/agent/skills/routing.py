from local_explorer_agent.app.domain.models import PlanCandidate
from local_explorer_agent.app.tools.route_tool import RouteTool


class RoutingSkill:
    name = "routing"

    def __init__(self, route_tool: RouteTool) -> None:
        self.route_tool = route_tool

    def run(self, candidate: PlanCandidate) -> PlanCandidate:
        route_segments: list[dict[str, object]] = []
        selected_pois = [stage.selected_poi for stage in candidate.stages if stage.selected_poi]
        for current, nxt in zip(selected_pois, selected_pois[1:], strict=False):
            result = self.route_tool.get_route(current.id, nxt.id)
            if result.success and result.data:
                route_segments.append(result.data)
        candidate.route_segments = route_segments
        return candidate
