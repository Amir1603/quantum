from .tfim_calculator import TFIMCalculator
from qiskit.quantum_info import Statevector, DensityMatrix
import numpy as np

class AnalyticalTFIM(TFIMCalculator):
    def __init__(self, N, J, h):
        if N != 2:
            raise ValueError("AnalyticalTFIM only supports N=2")

        super().__init__(N, J, h)

class MyCalculatorTFIM(AnalyticalTFIM):
    def __init__(self, N, J, h):
        super().__init__(N, J, h)

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
        # self.theta_E1 = 0.5 * np.arctan(-2 * self.h/self.J)
        # self.theta_E2 = 0.5 * np.arctan(self.h / self.J)
        # self.theta_q1 = 0.5 * np.arctan(-self.J / (2*self.h))
        # self.theta_q2 = -self.theta_q1

        # TODO - Go over rotation angle calculation and make sure it aligns with
        # Kazuki's calculated optimal rotation angle which yields the expected results.
        # Kazuki's rotation angle is calculated using his parameter k, which is 2k=J in my definition.
        k = self.J / 2
        rotation_angle = np.arcsin(
                (self.h * k) / np.sqrt((self.h**2 + 2 * k**2)**2 + self.h**2 * k**2)
            ) / 2
        self.theta_E1 = rotation_angle
        self.theta_q1 = rotation_angle

        self._init_n2_tfim_states_and_density_matrices()

    def _init_n2_tfim_states_and_density_matrices(self):
        """
        Calculates the ground state density matrix for the TFIM with N=2.
        The ground state is a pure state: |psi> = cos(gs_theta)|00> + sin(gs_theta)|11>.
        This method returns rho = |psi><psi|.
        """
        alpha, beta = MyCalculatorTFIM._alpha_beta(self.h, self.J)

        gs = [alpha, 0, 0, beta]
        self.gs0 = Statevector(gs)
        self.gs_rho = DensityMatrix(self.gs0)

        e1 = [0, 1/np.sqrt(2), -1/np.sqrt(2), 0]
        self.ex1 = Statevector(e1)
        self.ex1_rho = DensityMatrix(self.ex1)

    @staticmethod
    def _alpha_beta(h, J):
        Egs = -np.sqrt(4 * h**2 + J**2)
        alpha = J
        beta = Egs - 2 * h
        norm = np.sqrt(alpha**2 + beta**2)
        alpha /= norm
        beta /= norm

        return alpha, beta

class KazukiTFIM(AnalyticalTFIM):
    """
    Kazuki's TFIM class for N=2.
    """
    def __init__(self, N, J, h):
        super().__init__(N, J, h)
    
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
