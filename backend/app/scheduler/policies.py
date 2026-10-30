
import random
from abc import ABC, abstractmethod
from datetime import datetime, timezone

from app.models.job import Job, ExecutionTarget


class SchedulingPolicy(ABC):
    """Common interface for all scheduling policies."""

    @abstractmethod
    def decide(
        self,
        job: Job,
        classical_queue_len: int,
        quantum_queue_len: int,
    ) -> ExecutionTarget:
        pass


class RandomPolicy(SchedulingPolicy):
    """Baseline policy: choose either resource randomly."""

    def decide(
        self,
        job: Job,
        classical_queue_len: int,
        quantum_queue_len: int,
    ) -> ExecutionTarget:
        return random.choice([
            ExecutionTarget.CLASSICAL,
            ExecutionTarget.QUANTUM,
        ])


class GreedyCostLatencyPolicy(SchedulingPolicy):
    """Choose the resource with the lower weighted cost-latency score."""

    def __init__(
        self,
        cost_weight: float = 0.5,
        latency_weight: float = 0.5,
    ):
        if cost_weight < 0 or latency_weight < 0:
            raise ValueError("Weights cannot be negative")

        if cost_weight + latency_weight == 0:
            raise ValueError("At least one weight must be positive")

        self.cost_weight = cost_weight
        self.latency_weight = latency_weight

    def _score(
        self,
        runtime: float,
        cost_per_second: float,
        queue_len: int,
    ) -> float:
        estimated_cost = runtime * cost_per_second
        estimated_completion_time = runtime * (queue_len + 1)

        return (
            self.cost_weight * estimated_cost
            + self.latency_weight * estimated_completion_time
        )

    def decide(
        self,
        job: Job,
        classical_queue_len: int,
        quantum_queue_len: int,
    ) -> ExecutionTarget:
        if job.priority >= 4:
            classical_score = (
                job.classical_runtime * (classical_queue_len + 1)
            )
            quantum_score = (
                job.quantum_runtime * (quantum_queue_len + 1)
            )
        else:
            classical_score = self._score(
                job.classical_runtime,
                job.classical_cost_per_second,
                classical_queue_len,
            )
            quantum_score = self._score(
                job.quantum_runtime,
                job.quantum_cost_per_second,
                quantum_queue_len,
            )

        if classical_score <= quantum_score:
            return ExecutionTarget.CLASSICAL

        return ExecutionTarget.QUANTUM


class PredictiveDeadlineAwarePolicy(GreedyCostLatencyPolicy):
    """Choose resources using estimated completion time and deadlines."""

    def __init__(self,cost_weight: float=0.4, latency_weight: float=0.6):
        super().__init__(cost_weight=cost_weight, latency_weight=latency_weight)

    def decide(
        self,
        job: Job,
        classical_queue_len: int,
        quantum_queue_len: int,
    ) -> ExecutionTarget:
        greedy_choice = super().decide(
            job,
            classical_queue_len,
            quantum_queue_len,
        )

        if job.deadline is None:
            return greedy_choice

        now = datetime.now(timezone.utc)

        deadline = job.deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)

        seconds_remaining = (deadline - now).total_seconds()

        classical_time = job.classical_runtime * (
            classical_queue_len + 1
        )
        quantum_time = job.quantum_runtime * (
            quantum_queue_len + 1
        )

        classical_meets_deadline = (
            classical_time <= seconds_remaining
        )
        quantum_meets_deadline = (
            quantum_time <= seconds_remaining
        )

        # Only one resource can meet the deadline.
        if classical_meets_deadline and not quantum_meets_deadline:
            return ExecutionTarget.CLASSICAL

        if quantum_meets_deadline and not classical_meets_deadline:
            return ExecutionTarget.QUANTUM

        # Neither resource can meet the deadline.
        if not classical_meets_deadline and not quantum_meets_deadline:
            if classical_time <= quantum_time:
                return ExecutionTarget.CLASSICAL

            return ExecutionTarget.QUANTUM

        # Both resources can meet the deadline.
        # Preserve speed priority for high-priority jobs.
        if job.priority >= 4:
            if classical_time <= quantum_time:
                return ExecutionTarget.CLASSICAL

            return ExecutionTarget.QUANTUM

        # For lower-priority jobs, use the greedy cost-latency choice.
        return greedy_choice
