import time
from uuid import uuid4

from local_explorer_agent.app.repositories.booking_repository import BookingRepository
from local_explorer_agent.app.tools.base import BaseTool, ToolResult


class BookingTool(BaseTool):
    name = "booking_tool"

    def __init__(self, repository: BookingRepository) -> None:
        self.repository = repository

    def book(self, *, poi_id: str, action: str, params: dict[str, object]) -> ToolResult:
        started_at = time.perf_counter()
        mock_scenario = str(params.get("mock_scenario", "success"))
        if mock_scenario == "failed":
            return self._result(
                success=False,
                error_code="mock_booking_failed",
                error_message="Mock booking failed by scenario",
                started_at=started_at,
                mock_scenario=mock_scenario,
            )
        record = {
            "booking_id": f"bk_{uuid4().hex[:10]}",
            "poi_id": poi_id,
            "action": action,
            "status": "confirmed",
            "params": params,
        }
        self.repository.add_record(record)
        return self._result(data=record, started_at=started_at, mock_scenario=mock_scenario)
