
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict


class JobStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ExecutionTarget(str, Enum):
    UNASSIGNED = "unassigned"
    CLASSICAL = "classical"
    QUANTUM = "quantum"


class Job(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    job_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = "Unnamed Job"

    # Estimated workload characteristics
    classical_runtime: float = Field(gt=0)
    quantum_runtime: float = Field(gt=0)
    classical_cost_per_second: float = Field(default=0.02, ge=0)
    quantum_cost_per_second: float = Field(default=0.15, ge=0)

    priority: int = Field(default=3, ge=1, le=5)
    deadline: datetime | None = None
    num_qubits: int = Field(default=2, ge=1, le=20)

    # Runtime bookkeeping
    status: JobStatus = JobStatus.PENDING
    target: ExecutionTarget = ExecutionTarget.UNASSIGNED

    submitted_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    started_at: datetime | None = None
    completed_at: datetime | None = None

    actual_runtime: float | None = None
    result: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None

    @property
    def estimated_classical_cost(self) -> float:
        return self.classical_runtime * self.classical_cost_per_second

    @property
    def estimated_quantum_cost(self) -> float:
        return self.quantum_runtime * self.quantum_cost_per_second

    def wait_time(self) -> float | None:
        if self.started_at is None:
            return None
        return max(
            0.0,
            (self.started_at - self.submitted_at).total_seconds()
        )

    def turnaround_time(self) -> float | None:
        if self.completed_at is None:
            return None
        return max(
            0.0,
            (self.completed_at - self.submitted_at).total_seconds()
        )
