
import pytest

from app.workload_generator import generate_workload


def test_generates_requested_number_of_jobs():
    jobs = generate_workload(num_jobs=10)

    assert len(jobs) == 10


def test_seed_produces_repeatable_workloads():
    first = generate_workload(num_jobs=5, seed=123)
    second = generate_workload(num_jobs=5, seed=123)

    assert [
        (j.classical_runtime, j.quantum_runtime, j.priority)
        for j in first
    ] == [
        (j.classical_runtime, j.quantum_runtime, j.priority)
        for j in second
    ]


def test_burst_workload():
    jobs = generate_workload(num_jobs=5, arrival_mode="burst")

    assert len({job.submitted_at for job in jobs}) == 1


def test_invalid_workload_size():
    with pytest.raises(ValueError):
        generate_workload(num_jobs=0)


def test_invalid_arrival_mode():
    with pytest.raises(ValueError):
        generate_workload(arrival_mode="random")
