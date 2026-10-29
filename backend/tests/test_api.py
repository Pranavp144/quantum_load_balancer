
from fastapi.testclient import TestClient

from app.main import app, MANAGERS


client = TestClient(app)


def setup_function():
    for manager in MANAGERS.values():
        manager.metrics.jobs.clear()
        manager.completed_jobs.clear()


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_list_policies():
    response = client.get("/policies")

    assert response.status_code == 200
    assert set(response.json()["policies"]) == {
        "random",
        "greedy",
        "predictive",
    }


def test_submit_classical_friendly_job():
    response = client.post(
        "/jobs/submit?policy=greedy",
        json={
            "name": "API Test",
            "classical_runtime": 0.5,
            "quantum_runtime": 3.0,
            "priority": 3,
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["job"]["status"] == "completed"
    assert data["job"]["target"] == "classical"
    assert data["metrics"]["total_jobs"] == 1


def test_unknown_policy():
    response = client.post(
        "/jobs/submit?policy=unknown",
        json={
            "classical_runtime": 1.0,
            "quantum_runtime": 2.0,
        },
    )

    assert response.status_code == 400


def test_invalid_job_input():
    response = client.post(
        "/jobs/submit",
        json={
            "classical_runtime": -1,
            "quantum_runtime": 2,
        },
    )

    assert response.status_code == 422


def test_benchmark_endpoint():
    response = client.post(
        "/benchmark/run",
        json={
            "num_jobs": 2,
            "seed": 42,
            "arrival_mode": "burst",
        },
    )

    assert response.status_code == 200
    assert set(response.json()["results"]) == {
        "random",
        "greedy",
        "predictive",
    }
