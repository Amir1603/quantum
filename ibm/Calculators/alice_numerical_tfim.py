import numpy as np
from scipy.sparse import kron, eye, csc_matrix
from scipy.sparse.linalg import eigsh
import utils
from qiskit.quantum_info import Statevector, DensityMatrix
from .tfim_calculator import TFIMCalculator
from .numerical_tfim import NumericalTFIM

class AliceNumericalTFIM(NumericalTFIM):
    # Hamiltonian Construction for TFIM
    def _build_tfim_hamiltonian(self):
        H = csc_matrix((2**(self.N+1), 2**(self.N+1)), dtype=complex)
        for i in range(1, self.N+1):
            term = 1
            for j in range(self.N+1):
                term = kron(term, TFIMCalculator.X if j == i or j == 0 else TFIMCalculator.I)
            H += self.J * term

        for i in range(self.N+1):
            term = 1
            for j in range(self.N+1):
                term = kron(term, TFIMCalculator.Z if j == i else TFIMCalculator.I)
            H += self.h * term

        return H

    # Optimal Rotation Angles for Energy and Charge
    def _compute_optimal_rotation_angles(self):
        """
        Computes optimal rotation angles for general N.
        For energy, Bob's local energy is P_B = h*Z_N + J*X_0X_N.
        For charge, Bob's local charge is Q_B = (I+Z_N)/2.
        """
        exp_vals = self._raw_exp_vals

        num_theta_Ex = self.h * exp_vals.X0_Xbob - self.J * exp_vals.Zbob
        den_theta_Ex = self.h * exp_vals.Zbob + self.J * exp_vals.X0_Xbob
        # The minus sign in the denomenator doesn't affect the ratio, but just for choosign the right quadrant.
        theta_Ex = 0.5 * np.arctan2(num_theta_Ex, -den_theta_Ex)

        num_theta_qx = exp_vals.X0_Xbob
        den_theta_qx = 2*exp_vals.Zbob
        # The minus signs don't affect the ratio, but just for choosign the right quadrant.
        theta_qx = 0.5 * np.arctan2(-num_theta_qx, -den_theta_qx)

        # For this Hamiltonian, where the interaction is with Alice's site,
        # the protocol forbids working in different base for Alice other than X.
        theta_Ey = None
        theta_qy = None

        return theta_Ex, theta_qx, theta_Ey, theta_qy

    # Bob's Energy and Charge Expectation Calculation
    def _compute_bob_gs_energy_and_charge(self):
        energy_bob = self.h * self._raw_exp_vals.Zbob + self.J * self._raw_exp_vals.X0_Xbob
        charge_bob = 0.5 * (1 + self._raw_exp_vals.Zbob)

        return energy_bob, charge_bob
