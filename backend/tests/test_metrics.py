from datetime import datetime, timedelta, timezone

from app.models.job import Job, JobStatus, ExecutionTarget
from app.services.metrics import RunMetrics


def test_metrics_record_completed_job():
    job = Job(
        name="Metrics Test",
        classical_runtime=2.0,
        quantum_runtime=1.0,
    )

    now = datetime.now(timezone.utc)
    job.target = ExecutionTarget.CLASSICAL
    job.status = JobStatus.COMPLETED
    job.started_at = now
    job.completed_at = now + timedelta(seconds=2)
    job.actual_runtime = 2.0

    metrics = RunMetrics()
    metrics.record(job)

    summary = metrics.summary()

    assert summary["total_jobs"] == 1
    assert summary["classical_jobs"] == 1
    assert summary["quantum_jobs"] == 0
    assert summary["total_cost"] == 0.04


def test_empty_metrics_summary():
    summary = RunMetrics().summary()

    assert summary["total_jobs"] == 0
    assert summary["total_cost"] == 0.0