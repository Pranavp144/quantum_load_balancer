
import copy
import json
import time
from pathlib import Path

from app.models.job import Job
from app.scheduler.policies import (
    RandomPolicy,
    GreedyCostLatencyPolicy,
    PredictiveDeadlineAwarePolicy,
)
from app.services.queue_manager import QueueManager
from app.workload_generator import generate_workload


def run_benchmark(
    num_jobs: int = 20,
    seed: int = 42,
    arrival_mode: str = "steady",
    output_path: str | None = None,
) -> dict:
    """Compare all scheduling policies on identical workloads."""

    workload = generate_workload(
        num_jobs=num_jobs,
        seed=seed,
        arrival_mode=arrival_mode,
    )

    policies = {
        "random": RandomPolicy(),
        "greedy": GreedyCostLatencyPolicy(),
        "predictive": PredictiveDeadlineAwarePolicy(),
    }

    results = {}

    for name, policy in policies.items():
        jobs: list[Job] = copy.deepcopy(workload)
        manager = QueueManager(policy=policy)

        try:
            wall_start = time.perf_counter()
            manager.run_batch(jobs)
            wall_seconds = time.perf_counter() - wall_start

            results[name] = {
                **manager.summary(),
                "wall_clock_seconds": round(wall_seconds, 4),
            }
        finally:
            manager.shutdown()

    report = {
        "configuration": {
            "num_jobs": num_jobs,
            "seed": seed,
            "arrival_mode": arrival_mode,
        },
        "results": results,
    }

    if output_path:
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(report, indent=2),
            encoding="utf-8",
        )

    return report


if __name__ == "__main__":
    report = run_benchmark(
        num_jobs=20,
        seed=42,
        output_path="reports/benchmark_results.json",
    )

    print(json.dumps(report, indent=2))
