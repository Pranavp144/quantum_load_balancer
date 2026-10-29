from dataclasses import dataclass, field
from typing import Any

from app.models.job import Job, ExecutionTarget


@dataclass
class RunMetrics:
    jobs: list[dict[str, Any]] = field(default_factory=list)

    def record(self, job: Job) -> None:
        if job.status.value not in ("completed", "failed"):
            raise ValueError("Only finished jobs can be recorded")

        target = job.target.value

        if target not in ("classical", "quantum"):
            raise ValueError("Job has no valid execution target")

        cost_per_second = (
            job.classical_cost_per_second
            if job.target == ExecutionTarget.CLASSICAL
            else job.quantum_cost_per_second
        )

        runtime = job.actual_runtime or 0.0

        self.jobs.append({
            "job_id": job.job_id,
            "name": job.name,
            "status": job.status.value,
            "target": target,
            "actual_runtime": runtime,
            "cost": runtime * cost_per_second,
            "wait_time": job.wait_time() or 0.0,
            "turnaround_time": job.turnaround_time() or 0.0,
            "deadline_violated": (
                job.deadline is not None
                and job.completed_at is not None
                and job.completed_at > job.deadline
            ),
        })

    def summary(self) -> dict[str, Any]:
        total = len(self.jobs)

        if total == 0:
            return {
                "total_jobs": 0,
                "total_cost": 0.0,
                "average_wait_time": 0.0,
                "average_turnaround_time": 0.0,
                "deadline_violations": 0,
                "classical_jobs": 0,
                "quantum_jobs": 0,
                "failed_jobs": 0,
            }

        return {
            "total_jobs": total,
            "total_cost": sum(j["cost"] for j in self.jobs),
            "average_wait_time": sum(
                j["wait_time"] for j in self.jobs
            ) / total,
            "average_turnaround_time": sum(
                j["turnaround_time"] for j in self.jobs
            ) / total,
            "deadline_violations": sum(
                j["deadline_violated"] for j in self.jobs
            ),
            "classical_jobs": sum(
                j["target"] == "classical" for j in self.jobs
            ),
            "quantum_jobs": sum(
                j["target"] == "quantum" for j in self.jobs
            ),
            "failed_jobs": sum(
                j["status"] == "failed" for j in self.jobs
            ),
        }