
import threading

from app.models.job import Job, JobStatus, ExecutionTarget
from app.services.queue_manager import QueueManager, create_policy
from app.scheduler.policies import (
    RandomPolicy,
    GreedyCostLatencyPolicy,
    PredictiveDeadlineAwarePolicy,
)


class ClassicalOnlyPolicy:
    def decide(self, job, classical_queue_len, quantum_queue_len):
        return ExecutionTarget.CLASSICAL


class QuantumOnlyPolicy:
    def decide(self, job, classical_queue_len, quantum_queue_len):
        return ExecutionTarget.QUANTUM


def test_submit_job_end_to_end():
    job = Job(
        name="Integration Test",
        classical_runtime=5.0,
        quantum_runtime=0.5,
    )

    manager = QueueManager(policy=GreedyCostLatencyPolicy())
    try:
        result = manager.submit(job)

        assert result.status == JobStatus.COMPLETED
        assert result.target in (
            ExecutionTarget.CLASSICAL,
            ExecutionTarget.QUANTUM,
        )
        assert manager.summary()["total_jobs"] == 1
    finally:
        manager.shutdown()


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

    try:
        results = manager.run_batch(jobs)

        assert len(results) == 3
        assert manager.summary()["total_jobs"] == 3
    finally:
        manager.shutdown()


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


def test_classical_worker_concurrency():
    manager = QueueManager(
        policy=ClassicalOnlyPolicy(),
        classical_workers=2,
        quantum_workers=1,
    )

    active_workers = 0
    maximum_active_workers = 0
    lock = threading.Lock()

    original_execute = manager.classical_executor.execute

    def tracked_execute(job):
        nonlocal active_workers, maximum_active_workers

        with lock:
            active_workers += 1
            maximum_active_workers = max(
                maximum_active_workers,
                active_workers,
            )

        try:
            return original_execute(job)
        finally:
            with lock:
                active_workers -= 1

    manager.classical_executor.execute = tracked_execute

    jobs = [
        Job(
            name=f"Concurrent Job {i}",
            classical_runtime=1.0,
            quantum_runtime=2.0,
        )
        for i in range(4)
    ]

    try:
        results = manager.run_batch(jobs)

        assert len(results) == 4
        assert all(
            job.status == JobStatus.COMPLETED
            for job in results
        )
        assert maximum_active_workers == 2
        assert manager.summary()["total_jobs"] == 4
    finally:
        manager.shutdown()


def test_run_batch_preserves_submission_order():
    manager = QueueManager(policy=ClassicalOnlyPolicy())

    jobs = [
        Job(
            name=f"Order Job {i}",
            classical_runtime=1.0,
            quantum_runtime=2.0,
        )
        for i in range(5)
    ]

    try:
        results = manager.run_batch(jobs)

        assert [job.job_id for job in results] == [
            job.job_id for job in jobs
        ]
    finally:
        manager.shutdown()


def test_quantum_worker_limit():
    manager = QueueManager(
        policy=QuantumOnlyPolicy(),
        classical_workers=2,
        quantum_workers=1,
    )

    active_workers = 0
    maximum_active_workers = 0
    lock = threading.Lock()

    original_execute = manager.quantum_executor.execute

    def tracked_execute(job):
        nonlocal active_workers, maximum_active_workers

        with lock:
            active_workers += 1
            maximum_active_workers = max(
                maximum_active_workers,
                active_workers,
            )

        try:
            return original_execute(job)
        finally:
            with lock:
                active_workers -= 1

    manager.quantum_executor.execute = tracked_execute

    jobs = [
        Job(
            name=f"Quantum Job {i}",
            classical_runtime=2.0,
            quantum_runtime=1.0,
            num_qubits=2,
        )
        for i in range(3)
    ]

    try:
        results = manager.run_batch(jobs)

        assert len(results) == 3
        assert all(
            job.status == JobStatus.COMPLETED
            for job in results
        )
        assert all(
            job.target == ExecutionTarget.QUANTUM
            for job in results
        )
        assert maximum_active_workers == 1
        assert manager.summary()["total_jobs"] == 3
    finally:
        manager.shutdown()
