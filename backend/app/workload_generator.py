
import random
from datetime import datetime, timedelta, timezone

from app.models.job import Job


def generate_workload(
    num_jobs: int = 20,
    seed: int = 42,
    arrival_mode: str = "steady",
) -> list[Job]:
    """Generate reproducible synthetic jobs for benchmarking."""

    if num_jobs < 1:
        raise ValueError("num_jobs must be at least 1")

    if arrival_mode not in ("steady", "burst"):
        raise ValueError("arrival_mode must be 'steady' or 'burst'")

    rng = random.Random(seed)
    jobs = []
    base_time = datetime.now(timezone.utc)

    for i in range(num_jobs):
        quantum_friendly = rng.random() < 0.4

        if quantum_friendly:
            classical_runtime = rng.uniform(3.0, 8.0)
            quantum_runtime = rng.uniform(0.5, 2.0)
        else:
            classical_runtime = rng.uniform(0.2, 1.5)
            quantum_runtime = rng.uniform(1.0, 4.0)

        priority = rng.choices(
            population=[1, 2, 3, 4, 5],
            weights=[15, 25, 35, 15, 10],
            k=1,
        )[0]

        deadline = None
        if rng.random() < 0.3:
            deadline = base_time + timedelta(
                seconds=rng.uniform(2.0, 15.0)
            )

        submitted_at = base_time
        if arrival_mode == "steady":
            submitted_at += timedelta(seconds=i * 0.1)

        jobs.append(
            Job(
                name=f"Job-{i + 1}",
                classical_runtime=classical_runtime,
                quantum_runtime=quantum_runtime,
                priority=priority,
                deadline=deadline,
                submitted_at=submitted_at,
                num_qubits=rng.randint(2, 4),
            )
        )

    return jobs
