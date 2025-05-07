from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp, DensityMatrix
from qiskit_aer.library import SetDensityMatrix
from scipy.sparse.linalg import eigsh
import math
import numpy as np
import utils
from conf import Conf

class Observable:
    def __init__(self, name, conf: Conf):
        self.name = name
        self._conf = conf

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

        # The state vector is |psi> = [cos_t, 0, 0, sin_t]^T (for basis |00>, |01>, |10>, |11>)
        # The density matrix rho = |psi><psi|
        rho = np.zeros((4, 4), dtype=complex)
        rho[0, 0] = cos_t**2
        rho[0, 3] = cos_t * sin_t
        rho[3, 0] = cos_t * sin_t # rho is Hermitian, so rho[3,0] = conj(rho[0,3])
        rho[3, 3] = sin_t**2

        p_err = 0
        rho_err = np.zeros((4, 4), dtype=complex)

        if self._conf.p_bitflip_error != 0:
            X_bob = np.kron(np.array([[0, 1], [1, 0]]), np.eye(2))
            rho_err = X_bob @ rho @ X_bob
            p_err = self._conf.p_bitflip_error

        if self._conf.p_alice_phaseflip_error != 0:
            Z_alice = np.kron(np.eye(2), np.array([[1, 0], [0, -1]]))
            rho_err = Z_alice @ rho @ Z_alice
            p_err = self._conf.p_alice_phaseflip_error

        if self._conf.p_bob_phaseflip_error != 0:
            Z_bob = np.kron(np.array([[1, 0], [0, -1]]), np.eye(2))
            rho_err = Z_bob @ rho @ Z_bob
            p_err = self._conf.p_bob_phaseflip_error

        if self._conf.p_excited_mixture != 0:
            # This is the density matrix for the excited state sqrt(0.5)*(|01>-|10>)
            rho_err[1, 1] = 0.5
            rho_err[1, 2] = -0.5
            rho_err[2, 1] = -0.5
            rho_err[2, 2] = 0.5
            p_err = self._conf.p_excited_mixture

        rho_error = (1 - p_err) * rho + p_err * rho_err

        dm = DensityMatrix(rho_error)

        return dm

    @staticmethod
    def _get_n3_tfim_ground_state(k):
        """
        Numerically calculates the ground state vector for the N=3 TFIM.
        H = J*(X0X1 + X1X2) + Z0 + Z1 + Z2
        Caches the result based on J.
        """
        print(f"Calculating N=3 ground state for J={k}...")
        # Define Pauli strings for the N=3 Hamiltonian
        # Remember Qiskit orders qubits right-to-left (q2, q1, q0)
        paulis = [
            ("XXI", k), # X0*X1
            ("IXX", k), # X1*X2
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

    def apply_ground_state(self, qc: QuantumCircuit):
        """Prepares the ground state for the TFIM."""
        if self.N == 2:
            gs_dm = self._get_n2_tfim_ground_state_density_matrix()

            qc.append(SetDensityMatrix(gs_dm), list(range(self.N)))
        elif self.N == 3:
            gs_vector = Observable._get_n3_tfim_ground_state(self.k)

            # Qubits list [q0, q1, q2] corresponds to indices used in SparsePauliOp ('ZII' = Z on q0)
            qc.initialize(gs_vector, list(range(self.N)))
        else:
            raise NotImplementedError(f"Ground state prep not implemented for N={self.N}")

        # Add a barrier for clarity in the circuit
        qc.barrier()

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

        elif self.N == 3:
            try:
                gs_vector = Observable._get_n3_tfim_ground_state(self.k)
                if gs_vector is None: return None

                op_matrix = self._get_operator_matrix(pauli_string)
                if op_matrix is None: return None

                val = gs_vector.conj().T @ (op_matrix @ gs_vector)
                return np.real(val)
            except Exception as e:
                print(f"Error calculating N=3 GS expectation for {pauli_string}: {e}")
                return None
        else:
            print(f"GS expectation calculation not supported for N={self.N}")
            return None

    @staticmethod
    def calculate_n3_theta_params(conf: Conf):
        """
        Calculates xi, eta, and theta for N=3 based on ground state properties.
        Requires J (conf.k) to be set.
        Returns: tuple (xi, eta, theta) or (None, None, None) if N != 3 or error.
        """
        if conf.N != 3:
            return None, None, None
        if not hasattr(conf, 'k') or conf.k is None:
            print("Warning: Cannot calculate N=3 theta, J (conf.k) is not defined.")
            return None, None, None

        J = conf.k
        try:
            gs_vector = Observable._get_n3_tfim_ground_state(conf.k)
            if gs_vector is None: return None, None, None

            # --- Define Operators (N=3, Qiskit order q2, q1, q0) ---
            op_X0 = SparsePauliOp("XII")
            op_X1 = SparsePauliOp("IXI")
            op_X2 = SparsePauliOp("IIX")
            op_Z0 = SparsePauliOp("ZII")
            op_Z1 = SparsePauliOp("IZI")
            op_Z2 = SparsePauliOp("IIZ")

            # --- Calculate Expectation Values ---
            def expect(op: SparsePauliOp, vec: np.ndarray):
                # Calculate <vec| Op |vec> = vec.conj().T @ Op_matrix @ vec
                op_matrix = op.to_matrix(sparse=True)
                val = vec.conj().T @ (op_matrix @ vec)
                return np.real(val) # Expectation values should be real

            exp_Z0 = expect(op_Z0, gs_vector)
            exp_Z1 = expect(op_Z1, gs_vector)
            # exp_Z2 = expect(op_Z2, gs_vector) # Not needed for xi, eta directly but for H_B_gs

            # <X0*X2>
            op_X0X2 = op_X0.compose(op_X2) # Qiskit composition order
            exp_X0X2 = expect(op_X0X2, gs_vector)

            # <X0*X1*Z2>
            op_X0X1Z2 = op_X0.compose(op_X1).compose(op_Z2)
            exp_X0X1Z2 = expect(op_X0X1Z2, gs_vector)

            # --- Calculate xi and eta ---
            xi = exp_Z1 + 2 * exp_Z0
            eta = 2 * exp_X0X2 - 2 * J * exp_X0X1Z2

            # --- Calculate theta ---
            # atan2(y, x) handles quadrants correctly and x=0 case
            theta = 0.5 * np.arctan2(eta, xi)

            print(f"Calculated N=3 Params for J={J}: xi={xi:.4f}, eta={eta:.4f}, theta={theta:.4f}")
            return xi, eta, theta

        except Exception as e:
            print(f"Error calculating N=3 theta parameters: {e}")
            return None, None, None

    # --- Metadata ---
    def description(self):
        """Return a string description of the observable."""
        raise NotImplementedError()

    def __str__(self):
     return self.description()

