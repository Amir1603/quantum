from qiskit_aer import Aer
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import ClassicalRegister
from qiskit.quantum_info import SparsePauliOp
from qiskit.visualization import plot_histogram, circuit_drawer
from qiskit.primitives import BackendEstimatorV2
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit.primitives import BackendSamplerV2
import numpy as np


def initialize():
    service = QiskitRuntimeService()
    # Choose IBM Quantum backend
    backend = service.backend('ibm_brisbane')

    estimator = BackendEstimatorV2(backend=backend)
    sampler = BackendSamplerV2(backend=backend)

    return backend, sampler, estimator


def qet_circuit(h, k, apply_h,  num_qubits, name, backend):
    qc = QuantumCircuit(2, 2)

    # Prepare the ground state
    theta = -np.arccos(
        (1 / np.sqrt(2)) * np.sqrt(1 - h / np.sqrt(h**2 + k**2))
    )
    qc.ry(2 * theta, 0)
    qc.cx(0, 1)

    qc.h(0)
    
    # Alice's measurement
    qc.measure(0, 0)  # Measure qubit 0 into classical bit 0

    # Bob's conditional operation
    phi = np.arcsin(
        (h * k) / np.sqrt((h**2 + 2 * k**2)**2 + h**2 * k**2)
    ) / 2

    # Bob's conditional operation
    qc.ry(2 * phi, 1).c_if(0, 0)  # Apply U(+1) if classical bit 0 is 0
    qc.ry(-2 * phi, 1).c_if(0, 1)  # Apply U(-1) if classical bit 0 is 1

    if apply_h:
      qc.h(1)

    qc.measure(1, 1)  # Measure qubit 1 into classical bit 1

    cr = ClassicalRegister(num_qubits, name)
    qc.add_register(cr)  # Add the ClassicalRegister
    qc_transpiled = transpile(qc, backend)
    circuit_drawer(qc, output='mpl')

    return qc, qc_transpiled


def run_sim(qc, name, total_shots):
    # Use the Qiskit simulator
    simulator = Aer.get_backend('qasm_simulator')
    qc_compiled = transpile(qc, simulator)

    job_sim = simulator.run(qc_compiled, shots=total_shots)
    result_sim = job_sim.result()
    counts_sim = result_sim.get_counts(qc_compiled)

    counts_sim = {k.removeprefix('00 '): v for k, v in counts_sim.items()}

    print(f"{name} Simulation results:")
    print(counts_sim)
    plot_histogram(counts_sim)

    return counts_sim


def run_sampler(sampler, qc_transpiled, op, total_shots):
    op_sam = op.copy()
    op_sam.apply_layout(layout=qc_transpiled.layout)

    # Run the circuits and get quasi-probabilities
    pub = (qc_transpiled, [op_sam], None)
    job = sampler.run([qc_transpiled], shots=total_shots)
    return job.result()._pub_results[0].data.c.get_counts()


def run_estimator(estimator, qc_transpiled, op_str, op1, op2):
    num_qubits_transpiled = qc_transpiled.num_qubits
    op_expanded = SparsePauliOp.from_list([(op_str + "I" * (num_qubits_transpiled - len(op_str)), op1),
                                        ("I" * num_qubits_transpiled, op2)])

    pub = (qc_transpiled, [op_expanded], None)
    job = estimator.run([pub])
    return job.result()
