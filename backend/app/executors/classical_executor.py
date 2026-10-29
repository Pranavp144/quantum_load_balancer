
import random
import time

from app.models.job import (
    Job,
    JobStatus,
    ExecutionTarget,
)


class ClassicalExecutor:
    """Simulates execution of a job on a classical CPU worker."""

    def __init__(self, speed_factor: float = 1.0):
        if speed_factor <= 0:
            raise ValueError("speed_factor must be greater than zero")

        self.speed_factor = speed_factor

    def execute(self, job: Job) -> Job:
        if job.status == JobStatus.RUNNING:
            raise ValueError("Job is already running")

        job.target = ExecutionTarget.CLASSICAL
        job.status = JobStatus.RUNNING
        job.started_at = __import__(
            "datetime"
        ).datetime.now(
            __import__("datetime").timezone.utc
        )

        try:
            jitter = random.uniform(0.85, 1.15)

            simulated_runtime = (
                job.classical_runtime / self.speed_factor
            ) * jitter

            # Keep tests and demos fast.
            time.sleep(min(simulated_runtime, 0.05))

            job.actual_runtime = simulated_runtime
            job.result = {
                "executor": "classical",
                "simulated_runtime_seconds": round(
                    simulated_runtime, 4
                ),
            }

            job.status = JobStatus.COMPLETED
            return job

        except Exception as exc:
            job.status = JobStatus.FAILED
            job.error = str(exc)
            raise

        finally:
            job.completed_at = __import__(
                "datetime"
            ).datetime.now(
                __import__("datetime").timezone.utc
            )
