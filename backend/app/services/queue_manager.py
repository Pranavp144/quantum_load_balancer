
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
    """Coordinates scheduling, execution, and metrics collection."""

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

        self.metrics = RunMetrics()
        self.completed_jobs: list[Job] = []

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

        job.status = JobStatus.QUEUED

        try:
            if target == ExecutionTarget.CLASSICAL:
                result = self.classical_executor.execute(job)
            elif target == ExecutionTarget.QUANTUM:
                result = self.quantum_executor.execute(job)
            else:
                raise ValueError(f"Unsupported target: {target}")

        except Exception:
            # Executors mark failed jobs and preserve the error.
            if job.status == JobStatus.FAILED:
                self.metrics.record(job)
                self.completed_jobs.append(job)
            raise

        self.metrics.record(result)
        self.completed_jobs.append(result)

        return result

    def run_batch(self, jobs: list[Job]) -> list[Job]:
        results = []

        for job in jobs:
            results.append(self.submit(job))

        return results

    def summary(self) -> dict:
        return self.metrics.summary()


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
