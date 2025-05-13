from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
from qiskit_aer.library import SetDensityMatrix
from scipy.sparse.linalg import eigsh
import numpy as np
from conf import Conf
from Calculators.tfim_calculator import TFIMCalculator


class Observable:
    def __init__(self, name, conf: Conf, calc: TFIMCalculator):
        self.name = name
        self._conf = conf
        self._calc = calc

        # Cache for ground state vector to avoid recomputing
        self._gs_vector_cache = {}

    @property
    def h(self):
        return self._conf.h

    @property
    def k(self):
        return self._conf.k
    
    @property
    def theta(self):
        return self._conf.theta

    @property
    def N(self):
        return self._conf.N

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

    def apply_ground_state(self, qc: QuantumCircuit):
        """Prepares the ground state for the TFIM."""
        qc.append(SetDensityMatrix(self._calc.gs_rho), list(range(self.N)))

        # Add a barrier for clarity in the circuit
        qc.barrier()

    def _get_operator_matrix(self, pauli_string: str) -> np.ndarray | None:
        """Helper to get sparse matrix for a given Pauli string."""
        if len(pauli_string) != self.N:
            raise ValueError(f"Pauli string '{pauli_string}' length mismatch N={self.N}")
        try:
            op = SparsePauliOp(pauli_string)
            return op.to_matrix(sparse=True)
        except Exception as e:
            print(f"Error creating matrix for {pauli_string}: {e}")
            return None

    def get_theoretical_gs_expectation_value(self) -> float:
        """Calculates the theoretical ground state expectation value."""
        # This is a placeholder. The actual implementation should be in subclasses.
        raise NotImplementedError()

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

        gs_exp_val = self.get_theoretical_gs_expectation_value()

        # Calculate expectation value <O>
        expectation = sum_val / total_shots
        expectation = expectation - gs_exp_val

        # Normalize expectation value to get result in arbitrary units
        if gs_exp_val != 0:
            expectation /= abs(gs_exp_val)

        # Calculate <O^2>
        expectation_sq = sum_val_sq / total_shots

        # Calculate variance: Var(O) = <O^2> - <O>^2
        variance = max(0.0, expectation_sq - expectation**2)

        # Calculate SEM = sqrt(Var(O) / N)
        sem = np.sqrt(variance / total_shots) if total_shots > 0 else 0.0

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

