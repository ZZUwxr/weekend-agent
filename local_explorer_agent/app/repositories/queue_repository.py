from typing import Any

from local_explorer_agent.app.repositories.json_repository import JSONRepository


class QueueRepository(JSONRepository):
    filename = "queue_status.sample.json"

    def list_all(self) -> list[dict[str, Any]]:
        return self.load_json(self.filename)

    def get_status(self, poi_id: str) -> dict[str, Any]:
        for item in self.list_all():
            if item.get("poi_id") == poi_id:
                return item
        return {"poi_id": poi_id, "queue_minutes": 10, "risk": "medium", "mock_scenario": "default"}
