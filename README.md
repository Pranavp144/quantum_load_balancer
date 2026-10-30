# Quantum Load Balancer (QLB)

A cost-and-latency-aware scheduler for hybrid classical--quantum
workloads, built with **Python, FastAPI, Qiskit Aer, and Streamlit**.

QLB routes submitted jobs to either a classical execution path or a
simulated quantum backend. Scheduling decisions consider estimated
runtime, execution cost, job priority, queue-length inputs, and optional
deadlines.

> **Scope:** Quantum jobs run locally using the Qiskit Aer simulator.
> This project does not connect to physical quantum hardware. It is a
> focused academic prototype, not a production distributed orchestration
> platform.

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
-   **Concurrent resource pools:** Separate thread pools for classical
    and quantum jobs, with configurable worker limits.
-   **Metrics:** Execution cost, average wait time, turnaround time,
    deadline violations, resource distribution, and failed jobs.
-   **Workload generation:** Reproducible synthetic workloads with
    steady or burst arrival patterns.
-   **Benchmarking:** Compares all three policies using copies of the
    same generated workload.
-   **REST API:** FastAPI endpoints for health checks, policy listing,
    job submission, and benchmark execution.
-   **Streamlit frontend:** Browser dashboard for backend status, job
    submission, execution results, quantum measurement charts, and
    policy benchmark comparisons.
-   **Automated tests:** The backend test suite has 43 passing tests
    (last recorded project verification).

## Architecture

``` text
                 Streamlit Dashboard
                         |
                         v
                    FastAPI API
                         |
                         v
                     QueueManager
                         |
                         v
                  Scheduling Policy
                    /           \\
                   v             v
             Classical Pool   Quantum Pool
                   |             |
                   v             v
             Classical       Qiskit Aer
              Executor        Executor
                   \\             /
                    v           v
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
-   Streamlit
-   Requests
-   Plotly
-   Pandas
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
├── frontend/
│   ├── app.py
│   └── requirements.txt
├── docs/
├── reports/
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
python -m pip install -r frontend/requirements.txt
```

If `backend/requirements.txt` is not available in your checkout, install
the backend dependencies directly:

``` bash
python -m pip install fastapi "uvicorn[standard]" qiskit qiskit-aer pytest httpx
```

The frontend dependencies are listed in `frontend/requirements.txt`.

## Run the application

The backend and frontend run as two separate processes. Keep both
terminals open while using the dashboard.

### 1. Start the FastAPI backend

Open Terminal 1 from the repository root:

``` bash
source .venv/bin/activate
uvicorn app.main:app --app-dir backend --reload
```

The API will be available at:

-   API base URL: <http://127.0.0.1:8000>
-   Swagger UI: <http://127.0.0.1:8000/docs>
-   ReDoc: <http://127.0.0.1:8000/redoc>
-   Health check: <http://127.0.0.1:8000/health>

### 2. Start the Streamlit frontend

Open Terminal 2 from the repository root:

``` bash
source .venv/bin/activate
streamlit run frontend/app.py
```

Open the dashboard at <http://localhost:8501>.

The Streamlit app communicates with the local FastAPI service at
`http://127.0.0.1:8000`. Start the backend before using the frontend.

## Frontend capabilities

The Streamlit dashboard provides three sections:

-   **Dashboard:** Backend connection status, available scheduling
    policies, execution resources, and simulator scope.
-   **Submit Job:** Submit a job with runtime estimates, cost estimates,
    priority, number of qubits, optional deadline, and selected
    scheduling policy. View the chosen execution target, job status,
    runtime, policy metrics, and quantum measurement distribution when
    the quantum executor is selected.
-   **Benchmark:** Run a generated workload through Random, Greedy, and
    Predictive policies. View a comparison table and charts for total
    cost, average wait time, average turnaround time, and
    classical-versus-quantum job distribution.

The quantum measurement chart visualizes the bitstring counts returned
by the simulator. It does not demonstrate quantum advantage or a speedup
over physical quantum hardware.

## API endpoints

  ------------------------------------------------------------------------------
  Method                  Endpoint                       Purpose
  ----------------------- ------------------------------ -----------------------
  `GET`                   `/health`                      Check service health

  `GET`                   `/policies`                    List available
                                                         scheduling policies

  `POST`                  `/jobs/submit?policy=greedy`   Submit and execute a
                                                         job using the selected
                                                         policy

  `POST`                  `/benchmark/run`               Run a policy comparison
                                                         benchmark
  ------------------------------------------------------------------------------

Use Swagger UI at `/docs` to inspect request schemas and try the
endpoints.

### Example job request

``` json
{
  "name": "Quantum-friendly workload",
  "classical_runtime": 5.0,
  "quantum_runtime": 1.0,
  "classical_cost_per_second": 0.02,
  "quantum_cost_per_second": 0.15,
  "priority": 3,
  "num_qubits": 2
}
```

For example, submit it to:

``` text
POST http://127.0.0.1:8000/jobs/submit?policy=greedy
```

## Run tests

From the repository root:

``` bash
PYTHONPATH=backend pytest backend/tests/ -v
```

The last recorded backend test result was **43 tests passed**. Run the
suite again after making changes.

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

In this recorded run, Greedy had the lowest average wait and turnaround
times, while Predictive had a slightly lower total modeled cost. This
single run is illustrative, not a statistically conclusive performance
comparison. The Streamlit benchmark page runs a fresh benchmark, so its
values may differ.

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
-   The Streamlit frontend is a local demonstration interface and
    expects the FastAPI backend to be running separately.

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
-   [x] Streamlit dashboard
-   [x] Quantum measurement and benchmark visualizations
-   [x] Automated backend test suite (43 passing tests at last recorded
    verification)

Not included in the current scope:

-   [ ] Redis / Celery distributed task processing
-   [ ] Persistent job and benchmark storage
-   [ ] React frontend
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
