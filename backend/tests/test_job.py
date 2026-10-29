
from datetime import datetime, timedelta, timezone

from app.models.job import Job, JobStatus, ExecutionTarget


def test_job_defaults():
    job = Job(
        name="Test Job",
        classical_runtime=5.0,
        quantum_runtime=1.0,
    )

    assert job.status == JobStatus.PENDING
    assert job.target == ExecutionTarget.UNASSIGNED
    assert job.priority == 3
    assert job.job_id


def test_estimated_costs():
    job = Job(
        name="Cost Test",
        classical_runtime=5.0,
        quantum_runtime=1.0,
    )

    assert job.estimated_classical_cost == 0.1
    assert job.estimated_quantum_cost == 0.15


def test_wait_and_turnaround_time():
    submitted = datetime.now(timezone.utc)

    job = Job(
        name="Timing Test",
        classical_runtime=5.0,
        quantum_runtime=1.0,
        submitted_at=submitted,
    )

    job.started_at = submitted + timedelta(seconds=2)
    job.completed_at = submitted + timedelta(seconds=7)

    assert job.wait_time() == 2.0
    assert job.turnaround_time() == 7.0


def test_invalid_priority():
    from pydantic import ValidationError

    try:
        Job(
            name="Invalid Job",
            classical_runtime=5.0,
            quantum_runtime=1.0,
            priority=6,
        )
        assert False, "Expected validation to fail"
    except ValidationError:
        pass
