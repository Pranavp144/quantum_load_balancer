
from app.models.job import Job, JobStatus, ExecutionTarget
from app.executors.quantum_executor import QuantumExecutor


def test_quantum_circuit_execution():
    job = Job(
        name="Quantum Test",
        classical_runtime=5.0,
        quantum_runtime=1.0,
        num_qubits=2,
    )

    result = QuantumExecutor(shots=128).execute(job)

    assert result.status == JobStatus.COMPLETED
    assert result.target == ExecutionTarget.QUANTUM
    assert result.actual_runtime > 0
    assert result.result["executor"] == "quantum"
    assert result.result["shots"] == 128
    assert sum(result.result["counts"].values()) == 128
    assert result.result["distinct_outcomes"] >= 1


def test_quantum_circuit_measurements():
    executor = QuantumExecutor(shots=64)
    circuit = executor.build_circuit(3)

    assert circuit.num_qubits == 3
    assert circuit.num_clbits == 3
    assert circuit.count_ops().get("measure", 0) == 3


def test_invalid_shot_count():
    try:
        QuantumExecutor(shots=0)
        assert False, "Expected ValueError"
    except ValueError:
        pass
