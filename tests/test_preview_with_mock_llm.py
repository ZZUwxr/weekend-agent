from fastapi.testclient import TestClient

from local_explorer_agent.app.main import app


def test_family_and_friends_preview_with_default_mock_llm() -> None:
    client = TestClient(app)
    payloads = [
        {
            "user_id": "u001",
            "query": "今天下午想和老婆孩子出去玩几小时，别太远，老婆最近在减肥，孩子5岁",
            "city": "深圳",
            "start_time": "2026-05-10T14:00:00",
            "duration_minutes": 240,
            "location": {"lat": 22.54, "lon": 114.05},
        },
        {
            "user_id": "u002",
            "query": "周末2男2女想出去玩半天，想拍照但也别太折腾，预算别太高，最好有点氛围",
            "city": "深圳",
            "start_time": "2026-05-11T14:00:00",
            "duration_minutes": 240,
            "location": {"lat": 22.54, "lon": 114.05},
        },
    ]

    for payload in payloads:
        response = client.post("/api/v1/plans/preview", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["recommended_plan_id"]
        assert len(body["plan_candidates"]) == 3
