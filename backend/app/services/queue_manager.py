
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

from app.models.job import Job, JobStatus, ExecutionTarget
from app.executors.classical_executor import ClassicalExecutor
from app.executors.quantum_executor import QuantumExecutor
from app.scheduler.policies import (
    SchedulingPolicy,
    RandomPolicy,
    GreedyCostLatencyPolicy,
    PredictiveDeadlineAwarePolicy,
)
from app.services.metrics import RunMetrics


class QueueManager:
    """Coordinates scheduling, concurrent execution, and metrics."""

    def __init__(
        self,
        policy: SchedulingPolicy | None = None,
        classical_workers: int = 2,
        quantum_workers: int = 1,
    ):
        if classical_workers < 1 or quantum_workers < 1:
            raise ValueError("At least one worker per resource is required")

        self.policy = policy or GreedyCostLatencyPolicy()

        self.classical_executor = ClassicalExecutor()
        self.quantum_executor = QuantumExecutor()

        self.classical_workers = classical_workers
        self.quantum_workers = quantum_workers

        self.classical_pool = ThreadPoolExecutor(
            max_workers=classical_workers,
            thread_name_prefix="classical-worker",
        )
        self.quantum_pool = ThreadPoolExecutor(
            max_workers=quantum_workers,
            thread_name_prefix="quantum-worker",
        )

        self.metrics = RunMetrics()
        self.completed_jobs: list[Job] = []

        self._metrics_lock = Lock()

    def _execute_job(
        self,
        job: Job,
        target: ExecutionTarget,
    ) -> Job:
        try:
            if target == ExecutionTarget.CLASSICAL:
                result = self.classical_executor.execute(job)

            elif target == ExecutionTarget.QUANTUM:
                result = self.quantum_executor.execute(job)

            else:
                raise ValueError(f"Unsupported target: {target}")

        except Exception:
            if job.status == JobStatus.FAILED:
                with self._metrics_lock:
                    self.metrics.record(job)
                    self.completed_jobs.append(job)
            raise

        with self._metrics_lock:
            self.metrics.record(result)
            self.completed_jobs.append(result)

        return result

    def submit(
        self,
        job: Job,
        classical_queue_len: int = 0,
        quantum_queue_len: int = 0,
    ) -> Job:
        if job.status != JobStatus.PENDING:
            raise ValueError("Only pending jobs can be submitted")

        target = self.policy.decide(
            job,
            classical_queue_len,
            quantum_queue_len,
        )

        job.target = target
        job.status = JobStatus.QUEUED

        pool = (
            self.classical_pool
            if target == ExecutionTarget.CLASSICAL
            else self.quantum_pool
        )

        future = pool.submit(self._execute_job, job, target)
        return future.result()

    def run_batch(self, jobs: list[Job]) -> list[Job]:
        # Validate the complete batch before scheduling anything.
        if any(job.status != JobStatus.PENDING for job in jobs):
            raise ValueError("All batch jobs must be pending")

        futures = []
        classical_queue_len = 0
        quantum_queue_len = 0

        for job in jobs:
            target = self.policy.decide(
                job,
                classical_queue_len,
                quantum_queue_len,
            )

            job.target = target
            job.status = JobStatus.QUEUED

            if target == ExecutionTarget.CLASSICAL:
                classical_queue_len += 1
                pool = self.classical_pool
            elif target == ExecutionTarget.QUANTUM:
                quantum_queue_len += 1
                pool = self.quantum_pool
            else:
                raise ValueError(f"Unsupported target: {target}")

            futures.append(
                pool.submit(self._execute_job, job, target)
            )

        # Preserve original input order in returned results.
        return [future.result() for future in futures]

    def summary(self) -> dict:
        with self._metrics_lock:
            return self.metrics.summary()

    def shutdown(self) -> None:
        """Shut down both worker pools."""
        self.classical_pool.shutdown(wait=True)
        self.quantum_pool.shutdown(wait=True)


def create_policy(name: str) -> SchedulingPolicy:
    policies = {
        "random": RandomPolicy,
        "greedy": GreedyCostLatencyPolicy,
        "predictive": PredictiveDeadlineAwarePolicy,
    }

    try:
        return policies[name.lower()]()
    except KeyError:
        raise ValueError(
            f"Unknown policy '{name}'. "
            f"Available policies: {', '.join(policies)}"
        ) from None
