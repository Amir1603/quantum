from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
from scipy.sparse.linalg import eigsh
import math
import numpy as np
import utils
from conf import Conf

class Observable:
    def __init__(self, name, conf: Conf):
        self.name = name
        self.h = conf.h
        self.k = conf.k
        self.theta = conf.theta
        self.N = conf.N

        # Cache for ground state vector to avoid recomputing
        self._gs_vector_cache = {}

    def _get_n3_tfim_ground_state(self):
        """
        Numerically calculates the ground state vector for the N=3 TFIM.
        H = J*(X0X1 + X1X2) + Z0 + Z1 + Z2
        Caches the result based on J.
        """
        cache_key = self.k
        if cache_key in self._gs_vector_cache:
            return self._gs_vector_cache[cache_key]

        print(f"Calculating N=3 ground state for J={self.k}...")
        # Define Pauli strings for the N=3 Hamiltonian
        # Remember Qiskit orders qubits right-to-left (q2, q1, q0)
        paulis = [
            ("XXI", self.k), # X0*X1
            ("IXX", self.k), # X1*X2
            ("ZII", 1.0),         # Z0
            ("IZI", 1.0),         # Z1
            ("IIZ", 1.0)          # Z2
        ]
        hamiltonian_op = SparsePauliOp.from_list(paulis)
        hamiltonian_matrix = hamiltonian_op.to_matrix(sparse=True)

        # Find the eigenvalue and eigenvector for the ground state (lowest energy)
        # Using eigsh for sparse matrices, requesting the lowest eigenvalue (which='SA')
        try:
            eigenvalues, eigenvectors = eigsh(hamiltonian_matrix, k=1, which='SA')
            gs_vector = eigenvectors[:, 0]
            # Ensure normalization (eigsh should provide normalized vectors)
            gs_vector /= np.linalg.norm(gs_vector)
            self._gs_vector_cache[cache_key] = gs_vector
            print(f"Ground state calculated. Energy: {eigenvalues[0]}")
            return gs_vector
        except Exception as e:
            print(f"Error during N=3 ground state calculation: {e}")
            raise

    # --- Circuit Construction Methods (Keep as abstract or implement common logic) ---
    def apply_alice_measurement(self, qc: QuantumCircuit, alice_qubit, alice_creg):
        raise NotImplementedError()

    def apply_bob_operation(self, qc: QuantumCircuit, bob_qubit, alice_creg, xor_alice_res):
        raise NotImplementedError()

    def get_bob_measurement_basis(self):
        """Return 'X', 'Y', or 'Z' (or list for multi-qubit)"""
        raise NotImplementedError()

    def get_value(self, bitstring: str):
        """Calculate the observable's value for a given measurement bitstring."""
        raise NotImplementedError()

    def apply_ground_state(self, qc: QuantumCircuit, qubits: list):
        """Prepares the ground state for the TFIM."""
        if self.N == 2:
            denominator = np.sqrt(self.h**2 + self.k**2)
            if denominator == 0: raise ZeroDivisionError("N=2: h=k=0")
            gs_theta = -np.arccos((1 / np.sqrt(2)) * np.sqrt(1 - self.h / denominator))
            qc.ry(2 * gs_theta, qubits[utils.get_alice_qubit_idx(self.N)])
            qc.cx(qubits[utils.get_alice_qubit_idx(self.N)], qubits[utils.get_bob_qubit_idx(self.N)])
        elif self.N == 3:
            print(f"Preparing N=3 ground state for J={self.k} using numerical diagonalization.")
            gs_vector = self._get_n3_tfim_ground_state()

            # Qubits list [q0, q1, q2] corresponds to indices used in SparsePauliOp ('ZII' = Z on q0)
            qc.initialize(gs_vector, [qubits[i] for i in range(self.N)])
            qc.barrier() # Add barrier for visualization clarity
        else:
            raise NotImplementedError(f"Ground state prep not implemented for N={self.N}")

    def get_gs_expectation_value(self):
        # TODO: For simplicity currently this is the easiest way to add this functionality
        return 0

    # --- Post-Processing Calculations ---
    def calculate_expectation_and_sem(self, counts: dict, total_shots: int):
        """
        Calculates the expectation value and Standard Error of the Mean (SEM).
        Uses the get_value() method specific to the observable subclass.
        """
        if not counts or total_shots == 0:
            return 0.0, 0.0

        sum_val = 0.0
        sum_val_sq = 0.0

        for bitstring, count in counts.items():
            value = self.get_value(bitstring)
            sum_val += value * count
            sum_val_sq += (value**2) * count


        if total_shots <= 0:
             return 0.0, 0.0

        # Calculate expectation value <O>
        expectation = sum_val / total_shots
        expectation = expectation - self.get_gs_expectation_value()

        # Calculate <O^2>
        expectation_sq = sum_val_sq / total_shots

        # Calculate variance: Var(O) = <O^2> - <O>^2
        variance = max(0.0, expectation_sq - expectation**2)

        # Calculate SEM = sqrt(Var(O) / N)
        sem = math.sqrt(variance / total_shots) if total_shots > 0 else 0.0

        return expectation, sem

    def calculate_susceptibility(self, counts: dict):
        """Calculate susceptibility (often variance). Default: None."""
        # Default implementation returns None. Subclasses override if applicable.
        # Variance calculation is part of SEM, could reuse parts.
        total_shots = sum(counts.values())
        if not counts or total_shots == 0:
            return None

        sum_val = 0.0
        sum_val_sq = 0.0
        for bitstring, count in counts.items():
             try:
                value = self.get_value(bitstring)
                sum_val += value * count
                sum_val_sq += (value**2) * count
             except (KeyError, IndexError, ValueError):
                 total_shots -= count # Adjust as in SEM calc

        if total_shots <= 0: return None

        expectation = sum_val / total_shots
        expectation_sq = sum_val_sq / total_shots
        variance = max(0.0, expectation_sq - expectation**2)
        return variance # Default susceptibility definition as variance

    # --- Metadata ---
    def description(self):
        """Return a string description of the observable."""
        raise NotImplementedError()

    def __str__(self):
     return self.description()

