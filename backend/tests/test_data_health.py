from fastapi.testclient import TestClient

from local_explorer_agent.app.core.config import get_settings
from local_explorer_agent.app.main import app
from local_explorer_agent.app.repositories.data_health import check_data_health


def test_check_data_health_sample_data() -> None:
    settings = get_settings()
    data_dir = settings.data_dir if settings.data_dir.is_absolute() else settings.data_dir.resolve()

    health = check_data_health(data_dir)

    assert health["files"]["poi"]["exists"] is True
    assert health["files"]["poi"]["record_count"] > 0
    assert health["files"]["route_edges"]["exists"] is True
    assert "warnings" in health


def test_data_health_api() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/meta/data-health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["overall_status"] in {"ok", "warning", "degraded"}
    assert payload["files"]["poi"]["exists"] is True
    assert payload["files"]["poi"]["record_count"] > 0
