from .tfim_calculator import TFIMCalculator
from qiskit.quantum_info import Statevector, DensityMatrix
import numpy as np

class AnalyticalTFIM(TFIMCalculator):
    def __init__(self, N, J, h):
        if N != 2:
            raise ValueError("AnalyticalTFIM only supports N=2")

        super().__init__(N, J, h)

    @staticmethod
    def _alpha_beta(h, J):
        Egs = -np.sqrt(4 * h**2 + J**2)
        alpha = J
        beta = Egs - 2 * h
        norm = np.sqrt(alpha**2 + beta**2)
        alpha /= norm
        beta /= norm

        return alpha, beta

    def calc_all(self):
        # FIXME: Unused parameters for now? Complete when needed
        # self.E0 = -self.h / np.sqrt(self.h**2 + self.J**2) # Verify!
        self.E0 = None
        self.E1 = None
        self.total_charge = None

        # Used parameters for the TFIM
        self.total_energy = -np.sqrt(4 * self.h**2 + self.J**2)
        self.bob_energy = -(2 * self.h**2 + self.J**2) / np.sqrt(4 * self.h**2 + self.J**2)

        alpha, _ = AnalyticalTFIM._alpha_beta(self.h, self.J)
        self.bob_charge = alpha**2

        k = self.J / 2
        self.theta_E1 = np.arcsin(
                (self.h * k) / np.sqrt((self.h**2 + 2 * k**2)**2 + self.h**2 * k**2)
            ) / 2

        self.theta_q1 = 0.5 * np.arctan(-self.J / (2 * self.h))

        self._init_n2_tfim_states_and_density_matrices()

    def _init_n2_tfim_states_and_density_matrices(self):
        """
        Calculates the ground state density matrix for the TFIM with N=2.
        The ground state is a pure state: |psi> = cos(gs_theta)|00> + sin(gs_theta)|11>.
        This method returns rho = |psi><psi|.
        """
        alpha, beta = AnalyticalTFIM._alpha_beta(self.h, self.J)

        gs = [alpha, 0, 0, beta]
        self.gs0 = Statevector(gs)
        self.gs_rho = DensityMatrix(self.gs0)

        e1 = [0, 1/np.sqrt(2), -1/np.sqrt(2), 0]
        self.ex1 = Statevector(e1)
        self.ex1_rho = DensityMatrix(self.ex1)
