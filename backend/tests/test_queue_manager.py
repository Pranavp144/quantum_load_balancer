
from app.models.job import Job, JobStatus, ExecutionTarget
from app.services.queue_manager import QueueManager, create_policy
from app.scheduler.policies import (
    RandomPolicy,
    GreedyCostLatencyPolicy,
    PredictiveDeadlineAwarePolicy,
)


def test_submit_job_end_to_end():
    job = Job(
        name="Integration Test",
        classical_runtime=5.0,
        quantum_runtime=0.5,
    )

    manager = QueueManager(policy=GreedyCostLatencyPolicy())
    result = manager.submit(job)

    assert result.status == JobStatus.COMPLETED
    assert result.target in (
        ExecutionTarget.CLASSICAL,
        ExecutionTarget.QUANTUM,
    )
    assert manager.summary()["total_jobs"] == 1


def test_run_batch():
    manager = QueueManager(policy=GreedyCostLatencyPolicy())

    jobs = [
        Job(
            name=f"Job {i}",
            classical_runtime=2.0,
            quantum_runtime=1.0,
        )
        for i in range(3)
    ]

    results = manager.run_batch(jobs)

    assert len(results) == 3
    assert manager.summary()["total_jobs"] == 3


def test_create_policy():
    assert isinstance(create_policy("random"), RandomPolicy)
    assert isinstance(create_policy("greedy"), GreedyCostLatencyPolicy)
    assert isinstance(
        create_policy("predictive"),
        PredictiveDeadlineAwarePolicy,
    )


def test_unknown_policy():
    try:
        create_policy("unknown")
        assert False, "Expected ValueError"
    except ValueError:
        pass
