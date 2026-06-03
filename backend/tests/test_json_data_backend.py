from fastapi.testclient import TestClient

from local_explorer_agent.app.api import deps
from local_explorer_agent.app.main import app
from local_explorer_agent.app.repositories.poi_repository import POIRepository
from local_explorer_agent.app.repositories.queue_repository import QueueRepository
from local_explorer_agent.app.repositories.route_repository import RouteRepository


def _clear_all_deps_caches() -> None:
    for fn_name in (
        "get_settings",
        "get_plan_service",
        "get_orchestrator",
        "get_react_runtime",
        "get_poi_repository",
        "get_route_repository",
        "get_queue_repository",
        "get_weather_repository",
        "get_booking_repository",
        "get_user_memory_repository",
        "get_place_feedback_repository",
        "get_feedback_followup_repository",
        "get_poi_tool",
        "get_poi_query_tool",
        "get_route_tool",
        "get_queue_tool",
        "get_weather_tool",
        "get_execution_service",
        "get_feedback_service",
        "get_memory_update_service",
        "get_feedback_followup_service",
    ):
        fn = getattr(deps, fn_name, None)
        if fn is not None and hasattr(fn, "cache_clear"):
            fn.cache_clear()


def test_data_backend_env_is_ignored_and_json_repositories_are_used(monkeypatch) -> None:
    monkeypatch.setenv("DATA_BACKEND", "postgres")
    monkeypatch.setenv("DATABASE_URL", "postgresql://invalid/should_not_be_used")
    _clear_all_deps_caches()

    try:
        poi_repository = deps.get_poi_repository()
        route_repository = deps.get_route_repository()
        queue_repository = deps.get_queue_repository()

        assert isinstance(poi_repository, POIRepository)
        assert isinstance(route_repository, RouteRepository)
        assert isinstance(queue_repository, QueueRepository)
        assert poi_repository.search(city="深圳", limit=1)
    finally:
        _clear_all_deps_caches()


def test_runtime_meta_reports_json_only_backend(monkeypatch) -> None:
    monkeypatch.setenv("DATA_BACKEND", "postgres")
    monkeypatch.setenv("DATABASE_URL", "postgresql://invalid/should_not_be_used")
    _clear_all_deps_caches()

    try:
        response = TestClient(app).get("/api/v1/meta/runtime")
        payload = response.json()

        assert response.status_code == 200
        assert payload["data_backend"] == "json"
        assert "database_url_set" not in payload
    finally:
        _clear_all_deps_caches()
