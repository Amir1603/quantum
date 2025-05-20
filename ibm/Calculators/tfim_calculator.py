import utils
import numpy as np
import cmath
from qiskit.quantum_info import Statevector, DensityMatrix, partial_trace

class TFIMCalculator:
    def __init__(self, N, J, h):
        """
        Initialize the NumericalTFIM class with parameters for the transverse field Ising model.

        Parameters:
        N (int): Number of spins.
        J (float): Coupling constant.
        h (float): Transverse field strength.
        """
        self.N = N
        self.J = J
        self.h = h

        # More fields to be initialized by sub-classes calculations in `calc_all()`
        self.E0 = None
        self.gs0 = None
        self.E1 = None
        self.ex1 = None
        self.gs_rho = None
        self.ex1_rho = None
        self.bob_energy = None
        self.bob_charge = None
        self.theta_E1 = None
        self.theta_E2 = None
        self.theta_q1 = None
        self.theta_q2 = None

    def calc_all(self):
        """
        Calculate all properties of the transverse field Ising model.
        This method should be overridden by subclasses to perform specific calculations.
        """
        raise NotImplementedError("Subclasses should implement this method.")
    
    def apply_errors(self, conf):
        # Apply errors to the density matrix
        p_err = 0
        rho_err = np.zeros((2**conf.N, 2**conf.N), dtype=complex)

        if conf.p_depol_error != 0:
            rho_bob_reduced = partial_trace(self.gs_rho, [utils.get_bob_idx(self.N)])
            identity_alice_data = np.eye(2, dtype=complex) / 2
            rho_alice_mixed = DensityMatrix(identity_alice_data)

            rho_err = rho_alice_mixed.tensor(rho_bob_reduced)
            p_err = conf.p_depol_error

        if conf.p_bitflip_error != 0:
            X_bob = np.kron(np.array([[0, 1], [1, 0]]), np.eye(2))
            rho_err = X_bob @ self.gs_rho.data @ X_bob
            p_err = conf.p_bitflip_error

        if conf.p_alice_phaseflip_error != 0:
            Z_alice = np.kron(np.eye(2), np.array([[1, 0], [0, -1]]))
            rho_err = Z_alice @ self.gs_rho.data @ Z_alice
            p_err = conf.p_alice_phaseflip_error

        if conf.p_bob_phaseflip_error != 0:
            Z_bob = np.kron(np.array([[1, 0], [0, -1]]), np.eye(2))
            rho_err = Z_bob @ self.gs_rho.data @ Z_bob
            p_err = conf.p_bob_phaseflip_error

        if conf.p_excited_mixture != 0:
            rho_err = self.ex1_rho.data
            p_err = conf.p_excited_mixture

        if conf.p_excited_superposition_error != 0:
            p_err = conf.p_excited_superposition_error
            # Relative phase for the superposition is negligible according to QKD paper
            alpha = np.pi / 4
            # Amplitudes for the superposition
            amp_gs_super = np.sqrt(1 - p_err)
            amp_excited_super = cmath.exp(1j * alpha) * np.sqrt(p_err)

            # Superposition state vector: |psi> = amp_gs_super * |gs> + amp_excited_super * |E1>
            psi_superposition = (amp_gs_super * self.gs0.data) + (amp_excited_super * self.ex1.data)
            psi_superposition = psi_superposition / np.linalg.norm(psi_superposition)
            psi_superposition = Statevector(psi_superposition)

            rho_superposition = DensityMatrix(psi_superposition)

            # In this unique case, we don't need to calculate rho_err separately
            # because we are using the superposition state directly,
            # so we will use `p_err=1` to force `rho_error = rho_superposition`.
            p_err = 1
            rho_err = rho_superposition

        # Update the ground state's density matrix with the error
        self.gs_rho = DensityMatrix((1 - p_err) * self.gs_rho + p_err * rho_err)
