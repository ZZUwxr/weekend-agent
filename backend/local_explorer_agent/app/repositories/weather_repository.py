from typing import Any

from local_explorer_agent.app.repositories.json_repository import JSONRepository


class WeatherRepository(JSONRepository):
    filename = "weather.sample.json"

    def list_all(self) -> list[dict[str, Any]]:
        payload = self.load_json(self.filename)
        return payload if isinstance(payload, list) else [payload]

    def get_weather(self, city: str) -> dict[str, Any]:
        for item in self.list_all():
            if item.get("city") == city:
                return item
        return {"city": city, "condition": "晴天", "temperature": 26, "outdoor_fit": True}
