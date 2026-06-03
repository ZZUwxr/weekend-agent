import time
from uuid import uuid4

from local_explorer_agent.app.tools.base import BaseTool, ToolResult


class TaxiTool(BaseTool):
    name = "taxi_tool"

    def call_taxi(self, *, from_poi_id: str | None, to_poi_id: str | None) -> ToolResult:
        started_at = time.perf_counter()
        return self._result(
            data={
                "taxi_order_id": f"taxi_{uuid4().hex[:10]}",
                "from_poi_id": from_poi_id,
                "to_poi_id": to_poi_id,
                "status": "confirmed",
                "eta_minutes": 8,
            },
            started_at=started_at,
        )
