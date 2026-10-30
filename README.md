# Quantum Load Balancer (QLB)

A cost-and-latency-aware scheduler for hybrid classical--quantum
workloads, built with **Python, FastAPI, and Qiskit Aer**.

QLB routes submitted jobs to either a classical execution path or a
simulated quantum backend. Scheduling decisions consider estimated
runtime, execution cost, job priority, queue-length inputs, and optional
deadlines.

> **Scope:** Quantum jobs run locally using the Qiskit Aer simulator.
> This project does not require or connect to physical quantum hardware.
> It is a focused academic prototype, not a production distributed
> orchestration platform.

## Features

-   **Job lifecycle:** Tracks job details, priority, deadlines,
    execution target, status, timestamps, results, and errors.
-   **Classical executor:** Simulates classical execution time with
    small random variation.
-   **Quantum executor:** Builds, transpiles, and executes measured
    quantum circuits using Qiskit Aer.
-   **Three scheduling policies:**
    -   `random` --- baseline resource selection.
    -   `greedy` --- weighted cost-and-latency selection, with
        speed-first handling for high-priority jobs.
    -   `predictive` --- deadline-aware routing layered on the weighted
        policy.
-   **Concurrent resource pools:** Uses separate thread pools for
    classical and quantum jobs, with configurable worker limits.
-   **Metrics:** Reports execution cost, average wait time, turnaround
    time, deadline violations, resource distribution, and failed jobs.
-   **Workload generation:** Creates reproducible synthetic workloads
    with steady or burst arrival patterns.
-   **Benchmarking:** Compares the three policies using copies of the
    same generated workload.
-   **REST API:** FastAPI endpoints for health checks, policy listing,
    job submission, and benchmark execution.
-   **Automated tests:** The current project test suite has **43 passing
    tests**.

## Architecture

``` text
             Client / Workload Generator
                        |
                        v
                  FastAPI Service
                        |
                        v
                   QueueManager
                        |
                        v
                 Scheduling Policy
                  /             \
                 v               v
          Classical Pool    Quantum Pool
                 |               |
                 v               v
          Classical          Qiskit Aer
           Executor           Executor
                 \               /
                  v             v
                    Run Metrics
                        |
                        v
                 Benchmark Report
```

## Technology stack

-   Python 3.12+
-   FastAPI
-   Uvicorn
-   Pydantic
-   Qiskit
-   Qiskit Aer
-   pytest
-   HTTPX

## Project structure

``` text
quantum-load-balancer/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── benchmark.py
│   │   ├── workload_generator.py
│   │   ├── models/
│   │   │   └── job.py
│   │   ├── executors/
│   │   │   ├── classical_executor.py
│   │   │   └── quantum_executor.py
│   │   ├── scheduler/
│   │   │   └── policies.py
│   │   └── services/
│   │       ├── metrics.py
│   │       └── queue_manager.py
│   ├── tests/
│   └── requirements.txt
├── docs/
├── .gitignore
└── README.md
```

## Setup

Run these commands from the repository root on Linux or macOS:

``` bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
```

If `backend/requirements.txt` is not available in your checkout, install
the dependencies directly:

``` bash
python -m pip install fastapi "uvicorn[standard]" qiskit qiskit-aer pytest httpx
```

## Run tests

From the repository root:

``` bash
PYTHONPATH=backend pytest backend/tests/ -v
```

**Current verified result: 43 tests passed.**

Run the suite again after making changes.

## Run the API

Start the development server from the repository root:

``` bash
PYTHONPATH=backend python -m uvicorn app.main:app --reload --port 8000 --app-dir backend
```

Open the interactive API documentation:

-   Swagger UI: <http://127.0.0.1:8000/docs>
-   Health check: <http://127.0.0.1:8000/health>

### API endpoints

  ------------------------------------------------------------------------------
  Method                  Endpoint                       Purpose
  ----------------------- ------------------------------ -----------------------
  `GET`                   `/health`                      Check service health

  `GET`                   `/policies`                    List available
                                                         scheduling policies

  `POST`                  `/jobs/submit?policy=greedy`   Submit a job using the
                                                         selected policy

  `POST`                  `/benchmark/run`               Run a policy comparison
                                                         benchmark
  ------------------------------------------------------------------------------

Use the Swagger UI at `/docs` to inspect request schemas and try the
endpoints.

Example job request (field names should match the API schema):

``` json
{
  "name": "Quantum-friendly workload",
  "classical_runtime": 5.0,
  "quantum_runtime": 1.0,
  "priority": 3,
  "qubits": 2
}
```

## Run a benchmark

From the repository root:

``` bash
PYTHONPATH=backend python -m app.benchmark
```

The default benchmark generates 20 jobs and compares `random`, `greedy`,
and `predictive` policies. It writes a report to:

``` text
reports/benchmark_results.json
```

The benchmark can also be called from Python:

``` python
from app.benchmark import run_benchmark

report = run_benchmark(
    num_jobs=20,
    seed=42,
    arrival_mode="steady",
    output_path="reports/benchmark_results.json",
)

print(report)
```

The same seed generates comparable workload inputs for each policy. The
report includes modeled execution metrics and wall-clock duration. These
are different measurements and should be interpreted separately.

## Example benchmark results

One recorded 20-job run produced the following results. Results can vary
between runs because execution timing and simulator performance are
environment-dependent.

  Metric                     Random   Greedy   Predictive
  ------------------------ -------- -------- ------------
  Total cost                 0.7268   0.2805       0.2789
  Average wait time (s)      0.0001   0.1900       0.7871
  Average turnaround (s)     0.0094   0.2341       0.8477
  Deadline violations             0        0            0
  Failed jobs                     0        0            0
  Wall-clock time (s)        0.7324   0.7696       0.7593

In this run, Greedy had the lowest average wait and turnaround times.
Predictive had a slightly lower total modeled cost. This single run is
illustrative, not a statistically conclusive performance comparison.

## Current limitations

-   Queue estimates are based on queue lengths, not detailed runtime
    estimates for every waiting job.
-   The classical executor simulates runtime rather than performing
    CPU-intensive application work.
-   Qiskit Aer simulation time is not a prediction of real QPU hardware
    latency or provider queue time.
-   Runtime and cost estimates are supplied by the synthetic workload
    model; they are not learned from historical data.
-   The system uses in-memory execution pools and metrics; it does not
    provide distributed workers or persistent job storage.
-   The API is intended for local development. Authentication, rate
    limiting, and production hardening are not included.

## Project status

Implemented:

-   [x] Job model and lifecycle
-   [x] Classical and simulated quantum executors
-   [x] Random, Greedy, and Predictive scheduling policies
-   [x] Concurrent classical and quantum worker pools
-   [x] Metrics collection
-   [x] Synthetic workload generation
-   [x] Policy benchmarking
-   [x] FastAPI service
-   [x] Automated test suite (43 passing tests)

Not included in the current scope:

-   [ ] Redis / Celery distributed task processing
-   [ ] Persistent job and benchmark storage
-   [ ] React monitoring dashboard
-   [ ] Docker Compose deployment
-   [ ] Production authentication and deployment hardening

These are possible future extensions, not requirements for running the
current project.

## Development

Before committing changes, run:

``` bash
PYTHONPATH=backend pytest backend/tests/ -v
git status
```

Use small, meaningful commits that describe the change.

## License

No license has been selected yet. Add a `LICENSE` file before describing
the repository as open source.
