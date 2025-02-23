from qiskit_aer import Aer, AerSimulator
from qiskit_aer.noise import NoiseModel, phase_damping_error
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import ClassicalRegister, Delay
from qiskit.quantum_info import SparsePauliOp, DensityMatrix
from qiskit.visualization import plot_histogram, circuit_drawer
from qiskit.primitives import BackendEstimatorV2
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit.primitives import BackendSamplerV2
import numpy as np


def initialize(noise_model):
    service = QiskitRuntimeService()

    backend = AerSimulator(noise_model=noise_model) if noise_model else service.backend('ibm_brisbane')

    estimator = None if noise_model else BackendEstimatorV2(backend=backend)
    sampler = BackendSamplerV2(backend=backend)

    return backend, sampler, estimator


def qet_circuit(h, k, apply_h,  num_qubits, name, backend):
    """
    Constructs the quantum circuit for the QET experiment.

    Args:
      h: Parameter h for the Hamiltonian.
      k: Parameter k for the Hamiltonian.
      apply_h: Bool indicating wether to apply hadmard gate.
      num_qubits: The number of qubits for the circuit.
      name: The classical register name.
      backend: The backend to optimize and transpile the circuit for.

    Returns:
      qc: The constructed QuantumCircuit object.
      qc_transpiled: The transpiled quantum circuit object.
    """
    
    delay_time = 10000
    delay = Delay(delay_time)

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

    # Idle Bob’s qubit before he acts
    qc.append(delay, [1])

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


def create_noise_model(p_dephase):
    # Create dephasing error
    dephase_error = phase_damping_error(p_dephase)

    # Build the noise model
    noise_model = NoiseModel()
    noise_model.add_all_qubit_quantum_error(dephase_error, ['id', 'measure'])  # Affect idling and measurement steps

    return noise_model


def prep_error_mitigation(estimator):
    # estimator.options.default_shots = total_shots
    # estimator.options.twirling.enable_gates = True
    # estimator.options.twirling.num_randomizations = 64
    # estimator.options.twirling.shots_per_randomization = 100

    # estimator.options.dynamical_decoupling.enable = True
    # estimator.options.dynamical_decoupling.sequence_type = "XpXm"

    estimator.options.resilience.measure_mitigation = True
    estimator.options.resilience.measure_noise_learning.num_randomizations = 64
    estimator.options.resilience.measure_noise_learning.shots_per_randomization = 100

    # estimator.options.resilience.zne_mitigation = True
    # estimator.options.resilience.zne.noise_factors = (1, 3, 5)
    # estimator.options.resilience.zne.extrapolator = "exponential"

    estimator.options.resilience.zne_mitigation = True
    estimator.options.resilience.zne.amplifier = "pea"

    # estimator.options.resilience.pec_mitigation = True
    # estimator.options.resilience.pec.max_overhead = 100


def run_sim(qc, name, total_shots):
    # Use the Qiskit simulator
    simulator = Aer.get_backend('qasm_simulator')
    qc_compiled = transpile(qc, simulator)

    job_sim = simulator.run(qc_compiled, shots=total_shots)
    result_sim = job_sim.result()
    rho = result_sim.data()['density_matrix']
    counts_sim = result_sim.get_counts(qc_compiled)

    counts_sim = {k.removeprefix('00 '): v for k, v in counts_sim.items()}

    print(f"{name} Simulation results:")
    print(counts_sim)
    plot_histogram(counts_sim)

    return counts_sim, rho


def run_sampler(sampler, qc_transpiled, total_shots):
    job = sampler.run([qc_transpiled], shots=total_shots)

    result = job.result()
    counts = result._pub_results[0].data.c.get_counts()
    
    # Assuming 'counts' is a dictionary of measurement outcomes from the raw sampler
    total_counts = sum(counts.values())
    probabilities = {state: count / total_counts for state, count in counts.items()}

    # Construct the density matrix
    rho = DensityMatrix.from_label('00')  # Initialize with an arbitrary state
    for state, prob in probabilities.items():
        rho += prob * DensityMatrix.from_label(state)

    return counts, rho


def run_estimator(estimator, qc_transpiled, op_str, op1, op2):
    num_qubits_transpiled = qc_transpiled.num_qubits
    op_expanded = SparsePauliOp.from_list([(op_str + "I" * (num_qubits_transpiled - len(op_str)), op1),
                                        ("I" * num_qubits_transpiled, op2)])

    pub = (qc_transpiled, [op_expanded], None)
    job = estimator.run([pub])
    return job.result()
