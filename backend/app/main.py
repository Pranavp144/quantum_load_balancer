
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.models.job import Job
from app.services.queue_manager import QueueManager, create_policy
from app.benchmark import run_benchmark


app = FastAPI(
    title="Quantum Load Balancer",
    description=(
        "Cost-and-latency-aware scheduling for "
        "classical and simulated quantum workloads."
    ),
    version="1.0.0",
)

# Keep one manager per policy so metrics accumulate independently.
MANAGERS = {
    name: QueueManager(policy=create_policy(name))
    for name in ("random", "greedy", "predictive")
}


class JobSubmission(BaseModel):
    name: str = "Unnamed Job"
    classical_runtime: float = Field(gt=0)
    quantum_runtime: float = Field(gt=0)
    classical_cost_per_second: float = Field(default=0.02, ge=0)
    quantum_cost_per_second: float = Field(default=0.15, ge=0)
    priority: int = Field(default=3, ge=1, le=5)
    deadline: str | None = None
    num_qubits: int = Field(default=2, ge=1, le=20)


class BenchmarkRequest(BaseModel):
    num_jobs: int = Field(default=20, ge=1, le=100)
    seed: int = 42
    arrival_mode: str = "steady"


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/policies")
def list_policies():
    return {
        "policies": list(MANAGERS.keys()),
        "default": "greedy",
    }


@app.post("/jobs/submit")
def submit_job(
    request: JobSubmission,
    policy: str = "greedy",
):
    policy_name = policy.lower()

    if policy_name not in MANAGERS:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Unknown scheduling policy",
                "available_policies": list(MANAGERS.keys()),
            },
        )

    try:
        job = Job(**request.model_dump())
        result = MANAGERS[policy_name].submit(job)

        return {
            "job": result.model_dump(mode="json"),
            "metrics": MANAGERS[policy_name].summary(),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Job execution failed: {exc}",
        ) from exc


@app.post("/benchmark/run")
def benchmark(request: BenchmarkRequest):
    if request.arrival_mode not in ("steady", "burst"):
        raise HTTPException(
            status_code=400,
            detail="arrival_mode must be 'steady' or 'burst'",
        )

    try:
        return run_benchmark(
            num_jobs=request.num_jobs,
            seed=request.seed,
            arrival_mode=request.arrival_mode,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Benchmark failed: {exc}",
        ) from exc
