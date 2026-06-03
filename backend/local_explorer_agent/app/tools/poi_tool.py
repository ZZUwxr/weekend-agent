import time

from local_explorer_agent.app.repositories.poi_repository import POIRepository
from local_explorer_agent.app.tools.base import BaseTool, ToolResult


class POITool(BaseTool):
    name = "poi_tool"

    def __init__(self, repository: POIRepository) -> None:
        self.repository = repository

    def search_poi(
        self,
        *,
        city: str,
        tags: list[str] | None = None,
        categories: list[str] | None = None,
        indoor: bool | None = None,
        max_queue_risk: str | None = None,
        limit: int = 5,
        priority_categories: list[str] | None = None,
    ) -> ToolResult:
        started_at = time.perf_counter()
        data = self.repository.search(
            city=city,
            tags=tags,
            categories=categories,
            indoor=indoor,
            max_queue_risk=max_queue_risk,
            limit=limit,
            priority_categories=priority_categories,
        )
        if not data:
            return self._result(
                success=False,
                data=[],
                error_code="poi_data_empty",
                error_message="No POI records matched the query or POI data is missing",
                started_at=started_at,
                mock_scenario="data_missing_or_empty",
            )
        return self._result(data=data, started_at=started_at)

    def get_poi_detail(self, poi_id: str) -> ToolResult:
        started_at = time.perf_counter()
        poi = self.repository.get(poi_id)
        if poi is None:
            return self._result(
                success=False,
                error_code="poi_not_found",
                error_message=f"POI {poi_id} not found",
                started_at=started_at,
            )
        return self._result(data=poi, started_at=started_at)
