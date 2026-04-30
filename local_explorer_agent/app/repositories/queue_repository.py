from typing import Any

from local_explorer_agent.app.repositories.json_repository import JSONRepository


class QueueRepository(JSONRepository):
    filename = "queue_status.sample.json"
    supplement_filenames = ["queue_status.intent_supplement.json"]

    def list_all(self) -> list[dict[str, Any]]:
        records = list(self.load_json(self.filename))
        for filename in self.supplement_filenames:
            records.extend(self.load_json(filename, default=[]))
        return _dedupe_by_poi_id(records)

    def get_status(self, poi_id: str) -> dict[str, Any]:
        for item in self.list_all():
            if item.get("poi_id") == poi_id:
                return item
        return {"poi_id": poi_id, "queue_minutes": 10, "risk": "medium", "mock_scenario": "default"}


def _dedupe_by_poi_id(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for record in records:
        poi_id = record.get("poi_id") if isinstance(record, dict) else None
        if not poi_id:
            continue
        by_id[poi_id] = record
    return list(by_id.values())
