
import time
from datetime import datetime, timezone

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

from app.models.job import Job, JobStatus, ExecutionTarget


class QuantumExecutor:
    """Executes quantum circuits using the local Qiskit Aer simulator."""

    def __init__(self, shots: int = 512):
        if shots < 1:
            raise ValueError("shots must be at least 1")

        self.shots = shots
        self.simulator = AerSimulator()

    def build_circuit(self, num_qubits: int) -> QuantumCircuit:
        circuit = QuantumCircuit(num_qubits, num_qubits)

        # 1. Put each qubit into superposition.
        for qubit in range(num_qubits):
            circuit.h(qubit)

        # 2. Entangle neighboring qubits.
        for qubit in range(num_qubits - 1):
            circuit.cx(qubit, qubit + 1)

        # 3. Apply a reproducible parameterized rotation.
        for qubit in range(num_qubits):
            circuit.rz(0.785, qubit)

        # 4. Apply a second CNOT chain.
        for qubit in range(num_qubits - 1):
            circuit.cx(qubit, qubit + 1)

        # 5. Measure every qubit.
        circuit.measure(range(num_qubits), range(num_qubits))

        return circuit

    def execute(self, job: Job) -> Job:
        if job.status == JobStatus.RUNNING:
            raise ValueError("Job is already running")

        job.target = ExecutionTarget.QUANTUM
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc)

        start = time.perf_counter()

        try:
            circuit = self.build_circuit(job.num_qubits)
            compiled_circuit = transpile(circuit, self.simulator)

            simulation_result = self.simulator.run(
                compiled_circuit,
                shots=self.shots,
            ).result()

            counts = simulation_result.get_counts()

            elapsed = time.perf_counter() - start

            job.actual_runtime = elapsed
            job.result = {
                "executor": "quantum",
                "shots": self.shots,
                "counts": counts,
                "most_frequent_outcome": max(
                    counts, key=counts.get
                ),
                "distinct_outcomes": len(counts),
                "simulation_runtime_seconds": round(elapsed, 6),
            }

            job.status = JobStatus.COMPLETED
            return job

        except Exception as exc:
            job.status = JobStatus.FAILED
            job.error = str(exc)
            raise

        finally:
            job.completed_at = datetime.now(timezone.utc)
