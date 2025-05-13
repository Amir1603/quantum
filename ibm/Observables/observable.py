from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp, Statevector, DensityMatrix, partial_trace
from qiskit_aer.library import SetDensityMatrix
from scipy.sparse.linalg import eigsh
import math
import cmath
import numpy as np
from conf import Conf
from Calculators.tfim_calculator import TFIMCalculator
import utils


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

    def _get_n2_tfim_ground_state_density_matrix(self) -> np.ndarray:
        """
        Calculates the ground state density matrix for the TFIM with N=2.
        The ground state is a pure state: |psi> = cos(gs_theta)|00> + sin(gs_theta)|11>.
        This method returns rho = |psi><psi|.
        """
        denominator = np.sqrt(self.h**2 + self.k**2)
        if np.isclose(denominator, 0):
            # This case (h=0, k=0) means H=0, so any state is a ground state with E=0.
            # The formula for gs_theta would be ill-defined.
            # You need to decide on a specific ground state or raise an error.
            # The original code raised ZeroDivisionError.
            raise ZeroDivisionError("N=2: h=k=0, gs_theta formula is ill-defined. Cannot determine a unique ground state via this formula.")

        # Term for arccos: (1 / sqrt(2)) * sqrt(1 - h / sqrt(h^2 + k^2))
        # Ensure argument for sqrt is non-negative
        val_inside_sqrt = 1 - self.h / denominator
        if val_inside_sqrt < 0 and not np.isclose(val_inside_sqrt, 0):
            # This implies h_param / denominator > 1, which shouldn't happen if h_param, k_param are real
            # and k_param != 0 or h_param != 0.
            raise ValueError(f"Invalid value for sqrt calculation: h/denominator = {self.h/denominator} > 1.")
        val_inside_sqrt = max(0, val_inside_sqrt) # Clamp to non-negative for safety

        term_for_arccos = (1 / np.sqrt(2)) * np.sqrt(val_inside_sqrt)
        
        # Ensure argument for arccos is within [-1, 1]
        term_for_arccos = np.clip(term_for_arccos, -1.0, 1.0)
        
        gs_theta = -np.arccos(term_for_arccos)

        cos_t = np.cos(gs_theta)
        sin_t = np.sin(gs_theta)

        # The state vector is |gs> = [cos_t, 0, 0, sin_t]^T (for basis |00>, |01>, |10>, |11>)
        gs = np.zeros(4, dtype=complex)
        gs[0] = cos_t
        gs[3] = sin_t
        gs = Statevector(gs)

        rho_gs = DensityMatrix(gs)

        # First Excited State Vector: |E1> = (1/sqrt(2)) * (|01> - |10>)
        # |E1> = 0*|00> + (1/sqrt(2))|01> - (1/sqrt(2))|10> + 0*|11>
        e1 = np.zeros(4, dtype=complex)
        e1[1] = 1 / np.sqrt(2)
        e1[2] = -1 / np.sqrt(2)
        e1 = Statevector(e1)

        rho_e1 = DensityMatrix(e1)

        p_err = 0
        rho_err = np.zeros((4, 4), dtype=complex)

        if self._conf.p_depol_error != 0:
            rho_bob_reduced = partial_trace(rho_gs, [utils.get_bob_qubit_idx(self.N)])
            identity_alice_data = np.eye(2, dtype=complex) / 2
            rho_alice_mixed = DensityMatrix(identity_alice_data)

            rho_err = rho_alice_mixed.tensor(rho_bob_reduced)
            p_err = self._conf.p_depol_error

        if self._conf.p_bitflip_error != 0:
            X_bob = np.kron(np.array([[0, 1], [1, 0]]), np.eye(2))
            rho_err = X_bob @ rho_gs.data @ X_bob
            p_err = self._conf.p_bitflip_error

        if self._conf.p_alice_phaseflip_error != 0:
            Z_alice = np.kron(np.eye(2), np.array([[1, 0], [0, -1]]))
            rho_err = Z_alice @ rho_gs.data @ Z_alice
            p_err = self._conf.p_alice_phaseflip_error

        if self._conf.p_bob_phaseflip_error != 0:
            Z_bob = np.kron(np.array([[1, 0], [0, -1]]), np.eye(2))
            rho_err = Z_bob @ rho_gs.data @ Z_bob
            p_err = self._conf.p_bob_phaseflip_error

        if self._conf.p_excited_mixture != 0:
            rho_err = rho_e1
            p_err = self._conf.p_excited_mixture

        if self._conf.p_excited_superposition_error != 0:
            p_err = self._conf.p_excited_superposition_error
            # Relative phase for the superposition is negligible according to QKD paper
            alpha = np.pi / 4
            # Amplitudes for the superposition
            amp_gs_super = np.sqrt(1 - p_err)
            amp_excited_super = cmath.exp(1j * alpha) * np.sqrt(p_err)

            # Superposition state vector: |psi> = amp_gs_super * |gs> + amp_excited_super * |E1>
            psi_superposition = (amp_gs_super * gs.data) + (amp_excited_super * e1.data)
            psi_superposition = psi_superposition / np.linalg.norm(psi_superposition)
            psi_superposition = Statevector(psi_superposition)

            rho_superposition = DensityMatrix(psi_superposition)

            # In this unique case, we don't need to calculate rho_err separately
            # because we are using the superposition state directly,
            # so we will use `p_err=1` to force `rho_error = rho_superposition`.
            p_err = 1
            rho_err = rho_superposition

        rho_error = (1 - p_err) * rho_gs + p_err * rho_err

        dm = DensityMatrix(rho_error)

        return dm

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
        # TODO: Unify
        if self.N == 2:
            gs_dm = self._get_n2_tfim_ground_state_density_matrix()

            qc.append(SetDensityMatrix(gs_dm), list(range(self.N)))
        else:
            gs_vector = self._calc.gs0

            # Qubits list [q0, q1, q2] corresponds to indices used in SparsePauliOp ('ZII' = Z on q0)
            qc.initialize(gs_vector, list(range(self.N)))

        # Add a barrier for clarity in the circuit
        qc.barrier()

    def get_gs_expectation_value(self):
        raise NotImplementedError("Subclasses should implement this method to return the ground state expectation value.")

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

        gs_exp_val = self.get_gs_expectation_value()

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

    # TODO: What is the difference from `get_gs_expectation_value`??
    def calculate_gs_expectation(self, pauli_string: str) -> float | None:
        """Calculates the ground state expectation value for a given Pauli string."""
        if self.N == 2:
            # --- Add N=2 Analytical Calculation if needed ---
            # Example: <Z1>_gs = -h / sqrt(h^2+k^2)
            # Example: <X0X1>_gs = -k / sqrt(h^2+k^2)
            print("Warning: N=2 analytical GS expectation calculation not fully implemented in calculate_gs_expectation.")
            if pauli_string == "ZI": # <Z0> = <Z1>
                denominator = np.sqrt(self.h**2 + self.k**2)
                return -self.h / denominator if denominator != 0 else 0.0
            elif pauli_string == "IZ": # <Z1>
                denominator = np.sqrt(self.h**2 + self.k**2)
                return -self.h / denominator if denominator != 0 else 0.0
            elif pauli_string == "XX": # <X0X1>
                denominator = np.sqrt(self.h**2 + self.k**2)
                return -self.k / denominator if denominator != 0 else 0.0
            else:
                return 0.0 # Placeholder for other N=2 operators

        else:
            try:
                gs_vector = Observable._get_numerical_tfim_ground_state(self.N, self.h, self.k)
                if gs_vector is None: return None

                op_matrix = self._get_operator_matrix(pauli_string)
                if op_matrix is None: return None

                val = gs_vector.conj().T @ (op_matrix @ gs_vector)
                return np.real(val)
            except Exception as e:
                print(f"Error calculating arbitrary N GS expectation for {pauli_string}: {e}")
                return None

    # --- Metadata ---
    def description(self):
        """Return a string description of the observable."""
        raise NotImplementedError()

    def __str__(self):
     return self.description()

