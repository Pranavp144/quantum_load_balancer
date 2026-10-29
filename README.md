# Quantum Load Balancer (QLB)

A cost-and-latency-aware scheduler for hybrid classical–quantum workloads, built with Python, FastAPI, and Qiskit Aer.

QLB models a resource-management layer that routes submitted jobs to either a classical execution path or a simulated quantum backend. Scheduling decisions consider estimated runtime, execution cost, priority, queue-length inputs, and optional deadlines.

> **Scope note:** Quantum execution currently uses the local Qiskit Aer simulator. The project does not require real quantum hardware. The initial orchestration path is synchronous; distributed asynchronous workers and the React dashboard are planned extensions.

## Features

- **Job model:** Tracks workload estimates, priority, deadline, execution target, status, timestamps, and results.
- **Classical executor:** Simulates CPU runtime with small random jitter and records the simulated duration.
- **Quantum executor:** Builds and runs measured quantum circuits using Qiskit Aer.
- **Pluggable scheduling policies:**
  - `random` — baseline routing policy.
  - `greedy` — weighted cost-and-latency decision, with time-first handling for high-priority jobs.
  - `predictive` — starts with a greedy decision and can override it when the alternative resource is estimated to meet a deadline.
- **Metrics:** Tracks estimated execution cost, wait time, turnaround time, deadline violations, routing split, and failed jobs.
- **Workload generator:** Produces reproducible synthetic jobs with steady or burst arrival timestamps.
- **Benchmarking:** Runs policies against copies of the same generated workload.
- **REST API:** FastAPI endpoints for health checks, listing policies, submitting jobs, and running benchmarks.

## Architecture

```text
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
       /           \
      v             v
Classical         Quantum
Executor          Executor
      \             /
       v           v
         Run Metrics
              |
              v
      Benchmark Results
```

## Technology stack

- Python 3.12+
- FastAPI
- Uvicorn
- Pydantic
- Qiskit
- Qiskit Aer
- pytest
- HTTPX

## Project structure

```text
quantum-load-balancer/
├── backend/
│   ├── app/
│   │   ├── __init__.py
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

Run these commands from the repository root on Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install fastapi "uvicorn[standard]" qiskit qiskit-aer pytest httpx
```

If a `backend/requirements.txt` file is present, you can install from it instead:

```bash
python -m pip install -r backend/requirements.txt
```

## Run tests

From the repository root:

```bash
PYTHONPATH=backend pytest backend/tests/ -v
```

The core suite reached **29 passing tests** before the API integration tests were added. Re-run the command above after each change to verify the current state.

## Run the API

Start the development server from the repository root:

```bash
PYTHONPATH=backend python -m uvicorn app.main:app --reload --port 8000 --app-dir backend
```

Then open:

- API documentation: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

### Available endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Check service health |
| `GET` | `/policies` | List scheduling policies |
| `POST` | `/jobs/submit?policy=greedy` | Submit a job using a selected policy |
| `POST` | `/benchmark/run` | Compare policies on a generated workload |

Example job request:

```json
{
  "name": "Quantum-friendly workload",
  "classical_runtime": 5.0,
  "quantum_runtime": 1.0,
  "priority": 3,
  "num_qubits": 2
}
```

Send this JSON to `POST /jobs/submit?policy=greedy`.

## Run a benchmark

From the repository root:

```bash
PYTHONPATH=backend python -m app.benchmark
```

The benchmark can also be called from Python:

```python
from app.benchmark import run_benchmark

report = run_benchmark(
    num_jobs=20,
    seed=42,
    arrival_mode="steady",
    output_path="reports/benchmark_results.json",
)

print(report)
```

Using the same seed creates comparable synthetic workload inputs for each policy. Wall-clock simulator time and modeled execution cost are different measurements and should be interpreted separately.

## Current limitations

- The current `QueueManager` is synchronous; queue lengths passed to a policy do not yet represent a live asynchronous queue.
- The classical executor simulates runtime rather than performing CPU-intensive work.
- Qiskit Aer simulation time is not a prediction of real QPU hardware latency or provider queue time.
- Runtime and cost estimates are supplied by the workload model; they are not learned from historical data.
- Benchmark conclusions should be based on repeated runs and larger workloads, not a single small sample.
- The API is intended for local development; authentication, rate limiting, and production hardening are not yet included.

## Roadmap

- [x] Job model and lifecycle
- [x] Classical and quantum simulator executors
- [x] Three scheduling policies
- [x] Metrics collection and synchronous orchestration
- [x] Synthetic workload generation
- [x] Initial policy benchmarking
- [x] Initial FastAPI service implementation
- [ ] Validate API tests and end-to-end behavior
- [ ] Profile and optimize repeated quantum circuit compilation
- [ ] Add asynchronous workers with Redis and Celery
- [ ] Add persistent job and benchmark storage
- [ ] Build a React dashboard
- [ ] Add Docker Compose deployment
- [ ] Add CI and expanded performance experiments

## Development

Run the tests before committing:

```bash
PYTHONPATH=backend pytest backend/tests/ -v
git status
```

Use small, meaningful commits, for example:

```text
feat: implement QLB scheduling and benchmarking core
feat: expose scheduling through FastAPI
perf: optimize quantum circuit execution
feat: add asynchronous task processing
feat: add React monitoring dashboard
build: add Docker Compose deployment
docs: document architecture and benchmark results
```

## License

No license has been selected yet. Add a `LICENSE` file before describing the repository as open source.
