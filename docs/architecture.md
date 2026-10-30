# Quantum Load Balancer (QLB) --- System Architecture

## Overview

Quantum Load Balancer (QLB) is a Python-based prototype that routes
submitted workloads to either a classical executor or a simulated
quantum executor. A scheduling policy selects the execution target, the
QueueManager coordinates concurrent resource worker pools, and the
metrics service records execution outcomes.

Quantum execution is performed locally with Qiskit Aer. The current
implementation does not use physical quantum hardware.

## Architecture diagram

``` text
                 Client / Workload Generator
                            |
                            v
                      FastAPI Service
                 (REST API and policy choice)
                            |
                            v
                        QueueManager
                (job routing and coordination)
                            |
                            v
                    Scheduling Policy
                  /         |          \
                 /          |           \
                v           v            v
             Random       Greedy      Predictive
                  \         |          /
                   \        |         /
                    \       v        /
                     Resource Selection
                       /          \
                      v            v
             Classical Pool    Quantum Pool
                      |            |
                      v            v
             Classical         Qiskit Aer
              Executor          Executor
                      \            /
                       \          /
                        v        v
                       Run Metrics
                            |
                            v
                     Benchmark Results
```

## Main components

### 1. Client and workload generator

The client submits jobs through the REST API. The workload generator
creates synthetic jobs with runtime estimates, priorities, optional
deadlines, and arrival patterns for testing and benchmarking.

### 2. FastAPI service

The FastAPI application exposes endpoints for: - Checking service
health. - Listing available scheduling policies. - Submitting a job
using a selected policy. - Running a benchmark across scheduling
policies.

Interactive API documentation is available through Swagger UI at `/docs`
when the local server is running.

### 3. QueueManager

The QueueManager coordinates job submission, scheduling, execution, and
metric collection. It sends selected jobs to separate classical and
quantum thread pools. Worker limits control how many jobs can execute
concurrently on each resource.

### 4. Scheduling policies

QLB includes three policies:

-   **Random:** selects a classical or quantum target randomly and acts
    as a baseline.
-   **Greedy:** compares weighted cost and estimated completion-time
    scores. High-priority jobs prioritize faster completion.
-   **Predictive:** extends the weighted policy with deadline-aware
    resource selection. It estimates whether each resource can meet a
    job's deadline and selects accordingly.

The policy estimates use the queue-length information supplied by the
QueueManager. They are simplified estimates rather than a detailed
simulation of every waiting job.

### 5. Execution pools and executors

**Classical worker pool** - Runs jobs through the ClassicalExecutor. -
Simulates execution duration with a small random variation. - Records
the job's execution result and lifecycle timestamps.

**Quantum worker pool** - Runs jobs through the QuantumExecutor. -
Builds and measures quantum circuits. - Uses Qiskit Aer to simulate
circuit execution locally. - Records measurement results and execution
information.

The quantum path is a simulator-based execution path, not access to a
real quantum processing unit.

### 6. Run metrics

The metrics service records completed and failed jobs and produces
summary values such as: - Total execution cost. - Average wait time. -
Average turnaround time. - Deadline violations. - Number of classical
and quantum jobs. - Failed job count.

### 7. Benchmarking

The benchmark runner generates a workload and gives each scheduling
policy a copy of the same jobs. It records each policy's metrics and
wall-clock duration so their behavior can be compared under the same
workload inputs.

## Job execution flow

1.  A client submits a job or a workload is generated.
2.  FastAPI receives the request.
3.  QueueManager passes the job and queue-length information to the
    selected scheduling policy.
4.  The policy chooses the classical or quantum execution target.
5.  QueueManager submits the job to the corresponding worker pool.
6.  The executor processes the job and updates its status and result.
7.  RunMetrics records the outcome.
8.  The API returns the response, or the benchmark runner collects the
    summary.

## Implementation scope and limitations

-   Classical execution is simulated; it does not run a user-provided
    CPU workload.
-   Quantum circuits are simulated locally with Qiskit Aer; no physical
    QPU is connected.
-   Scheduling uses simplified runtime and queue-length estimates.
-   Jobs and metrics are held in memory; persistent storage and
    distributed task processing are not part of the current
    implementation.
-   The architecture is intended as an academic prototype and local
    demonstration, not a production-ready distributed scheduler.
