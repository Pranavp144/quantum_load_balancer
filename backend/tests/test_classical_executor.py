
from app.models.job import Job, JobStatus, ExecutionTarget
from app.executors.classical_executor import ClassicalExecutor


def test_classical_execution_completes():
    job = Job(
        name="CPU Test",
        classical_runtime=2.0,
        quantum_runtime=1.0,
    )

    result = ClassicalExecutor().execute(job)

    assert result.status == JobStatus.COMPLETED
    assert result.target == ExecutionTarget.CLASSICAL
    assert result.actual_runtime > 0
    assert result.result["executor"] == "classical"
    assert result.started_at is not None
    assert result.completed_at is not None


def test_speed_factor_changes_simulated_runtime():
    job = Job(
        name="Fast CPU Test",
        classical_runtime=2.0,
        quantum_runtime=1.0,
    )

    executor = ClassicalExecutor(speed_factor=2.0)
    result = executor.execute(job)

    assert 0.85 <= result.actual_runtime <= 1.15


def test_invalid_speed_factor():
    try:
        ClassicalExecutor(speed_factor=0)
        assert False, "Expected ValueError"
    except ValueError:
        pass
