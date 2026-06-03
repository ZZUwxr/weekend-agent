from typing import Any

from local_explorer_agent.app.repositories.json_repository import JSONRepository


class UserProfileRepository(JSONRepository):
    filename = "user_profiles.sample.json"

    def list_all(self) -> list[dict[str, Any]]:
        return self.load_json(self.filename)

    def get(self, user_id: str) -> dict[str, Any] | None:
        return next((item for item in self.list_all() if item.get("user_id") == user_id), None)
