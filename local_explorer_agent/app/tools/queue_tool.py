import time

from local_explorer_agent.app.repositories.queue_repository import QueueRepository
from local_explorer_agent.app.tools.base import BaseTool, ToolResult


class QueueTool(BaseTool):
    name = "queue_tool"

    def __init__(self, repository: QueueRepository) -> None:
        self.repository = repository

    def get_queue_status(self, poi_id: str) -> ToolResult:
        started_at = time.perf_counter()
        return self._result(data=self.repository.get_status(poi_id), started_at=started_at)
