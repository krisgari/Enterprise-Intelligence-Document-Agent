from fastapi.testclient import TestClient
from ragagent.api.app import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_query_blocked_on_pii_input():
    response = client.post("/query", json={"query": "my email is a@b.com, what's the policy?"})
    assert response.status_code == 200
    body = response.json()
    assert body["allowed"] is False


def test_trace_not_found_returns_404():
    response = client.get("/traces/nonexistent-id")
    assert response.status_code == 404
