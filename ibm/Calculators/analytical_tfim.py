from .tfim_calculator import TFIMCalculator
import cmath
import utils
from qiskit.quantum_info import Statevector, DensityMatrix, partial_trace
import numpy as np

class AnalyticalTFIM(TFIMCalculator):
    def __init__(self, N, J, h, conf):
        if N != 2:
            raise ValueError("AnalyticalTFIM only supports N=2")

        super().__init__(N, J, h)
        self._conf = conf

class MyCalculatorTFIM(AnalyticalTFIM):
    def __init__(self, N, J, h, conf):
        super().__init__(N, J, h, conf)

    def calc_all(self):
        # FIXME: Unused parameters for now? Complete when needed
        # self.E0 = -self.h / np.sqrt(self.h**2 + self.J**2) # Verify!
        self.E0 = None
        self.E1 = None
        self.total_charge = None

        # Used parameters for the TFIM
        self.total_energy = -np.sqrt(4 * self.h**2 + self.J**2)
        self.bob_energy = -(2 * self.h**2 + self.J**2) / np.sqrt(4 * self.h**2 + self.J**2)
        # self.bob_energy = -(self.h**2) / np.sqrt(self.h**2 + self.J**2)

        alpha, _ = MyCalculatorTFIM._alpha_beta(self.h, self.J)
        self.bob_charge = alpha**2

        # self.theta_E1 = 0.5 * np.arctan((3 * self.h * self.J) / (-(2 * self.h**2 + self.J**2)))
        self.theta_E1 = 0.5 * np.arctan(-2 * self.h/self.J)
        self.theta_E2 = 0.5 * np.arctan(self.h / self.J)
        self.theta_q1 = 0.5 * np.arctan(-self.J / (2*self.h))
        self.theta_q2 = -self.theta_q1

        self._init_n2_tfim_states_and_density_matrices()

    def _init_n2_tfim_states_and_density_matrices(self):
        """
        Calculates the ground state density matrix for the TFIM with N=2.
        The ground state is a pure state: |psi> = cos(gs_theta)|00> + sin(gs_theta)|11>.
        This method returns rho = |psi><psi|.
        """

        alpha, beta = MyCalculatorTFIM._alpha_beta(self.h, self.J)
        gs_vector = Statevector([alpha, 0, 0, beta])

        self.gs0 = gs_vector
        self.gs_rho = DensityMatrix(np.outer(gs_vector.data, np.conj(gs_vector.data)))

        e1_vector = Statevector([0, 1/np.sqrt(2), -1/np.sqrt(2), 0])
        self.ex1 = e1_vector
        self.ex1_rho = DensityMatrix(np.outer(e1_vector.data, np.conj(e1_vector.data)))

        return

        denominator = np.sqrt(self.h**2 + self.J**2)
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
        gs_vector = Statevector(gs)

        rho_gs = DensityMatrix(gs_vector)

        # First Excited State Vector: |E1> = (1/sqrt(2)) * (|01> - |10>)
        # |E1> = 0*|00> + (1/sqrt(2))|01> - (1/sqrt(2))|10> + 0*|11>
        e1 = np.zeros(4, dtype=complex)
        e1[1] = 1 / np.sqrt(2)
        e1[2] = -1 / np.sqrt(2)
        ex1_vector = Statevector(e1)

        ex1_rho = DensityMatrix(ex1_vector)

        # Apply errors to the density matrix
        p_err = 0
        rho_err = np.zeros((4, 4), dtype=complex)

        if self._conf.p_depol_error != 0:
            rho_bob_reduced = partial_trace(rho_gs, [utils.get_bob_idx(self.N)])
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
            rho_err = ex1_rho.data
            p_err = self._conf.p_excited_mixture

        if self._conf.p_excited_superposition_error != 0:
            p_err = self._conf.p_excited_superposition_error
            # Relative phase for the superposition is negligible according to QKD paper
            alpha = np.pi / 4
            # Amplitudes for the superposition
            amp_gs_super = np.sqrt(1 - p_err)
            amp_excited_super = cmath.exp(1j * alpha) * np.sqrt(p_err)

            # Superposition state vector: |psi> = amp_gs_super * |gs> + amp_excited_super * |E1>
            psi_superposition = (amp_gs_super * gs) + (amp_excited_super * e1)
            psi_superposition = psi_superposition / np.linalg.norm(psi_superposition)
            psi_superposition = Statevector(psi_superposition)

            rho_superposition = DensityMatrix(psi_superposition)

            # In this unique case, we don't need to calculate rho_err separately
            # because we are using the superposition state directly,
            # so we will use `p_err=1` to force `rho_error = rho_superposition`.
            p_err = 1
            rho_err = rho_superposition

        rho_error = (1 - p_err) * rho_gs + p_err * rho_err

        self.gs0 = gs_vector
        self.gs_rho = DensityMatrix(rho_error)
        self.ex1 = ex1_vector
        self.ex1_rho = ex1_rho

    @staticmethod
    def _alpha_beta(h, J):
        sqrt_term = np.sqrt(4 * h**2 + J**2)
        alpha = 2 * h - sqrt_term
        beta = J
        norm = np.sqrt(alpha**2 + beta**2)
        alpha /= norm
        beta /= norm

        return alpha, beta

class KazukiTFIM(AnalyticalTFIM):
    """
    Kazuki's TFIM class for N=2.
    """
    def __init__(self, N, J, h, conf):
        super().__init__(N, J, h, conf)
    
    def calc_all(self):
        # FIXME: Unused parameters for now? Complete when needed
        # self.E0 = -self.h / np.sqrt(self.h**2 + self.J**2) # Verify!
        self.E0 = None
        self.E1 = None
        self.total_charge = None
        self.total_energy = None
        self.theta_E2 = None
        self.theta_q2 = None

        # Used parameters for the TFIM
        self.bob_energy = -(self.h**2 + 2 * self.J**2) / np.sqrt(self.h**2 + self.J**2)
        self.bob_charge = 0.5 * (1.0 - self.h / np.sqrt(self.h**2 + self.J**2))

        rotation_angle = np.arcsin(
                (self.h * self.J) / np.sqrt((self.h**2 + 2 * self.J**2)**2 + self.h**2 * self.J**2)
            ) / 2
        self.theta_E1 = rotation_angle
        self.theta_q1 = rotation_angle

        self._init_n2_tfim_states_and_density_matrices()

    def _init_n2_tfim_states_and_density_matrices(self):
        denominator = np.sqrt(self.h**2 + self.J**2)
        val_inside_sqrt = 1 - self.h / denominator
        term_for_arccos = (1 / np.sqrt(2)) * np.sqrt(val_inside_sqrt)
        gs_theta = -np.arccos(term_for_arccos)
        gs_vector = Statevector([np.cos(gs_theta), 0, 0, np.sin(gs_theta)])

        self.gs0 = gs_vector
        self.gs_rho = DensityMatrix(np.outer(gs_vector.data, np.conj(gs_vector.data)))

        e1_vector = Statevector([0, 1/np.sqrt(2), -1/np.sqrt(2), 0])
        self.ex1 = e1_vector
        self.ex1_rho = DensityMatrix(np.outer(e1_vector.data, np.conj(e1_vector.data)))
