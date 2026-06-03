import time

from local_explorer_agent.app.repositories.weather_repository import WeatherRepository
from local_explorer_agent.app.tools.base import BaseTool, ToolResult


class WeatherTool(BaseTool):
    name = "weather_tool"

    def __init__(self, repository: WeatherRepository) -> None:
        self.repository = repository

    def get_weather(self, city: str) -> ToolResult:
        started_at = time.perf_counter()
        return self._result(data=self.repository.get_weather(city), started_at=started_at)
