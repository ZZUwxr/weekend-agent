from typing import Any

from local_explorer_agent.app.repositories.json_repository import JSONRepository


class RouteRepository(JSONRepository):
    filename = "route_edges.sample.json"

    def list_all(self) -> list[dict[str, Any]]:
        return self.load_json(self.filename)

    def get_route(self, from_poi_id: str, to_poi_id: str) -> dict[str, Any] | None:
        for edge in self.list_all():
            if edge.get("from") == from_poi_id and edge.get("to") == to_poi_id:
                return edge
            if edge.get("from") == to_poi_id and edge.get("to") == from_poi_id:
                return {**edge, "from": from_poi_id, "to": to_poi_id}
        return None
