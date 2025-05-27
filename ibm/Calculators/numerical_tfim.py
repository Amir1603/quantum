import numpy as np
from scipy.sparse import kron, eye, csc_matrix
from scipy.sparse.linalg import eigsh
import utils
from qiskit.quantum_info import Statevector, DensityMatrix
from .tfim_calculator import TFIMCalculator

class NumericalTFIM(TFIMCalculator):
    def __init__(self, N, J, h):
        super().__init__(N, J, h)
        self.H = self._build_tfim_hamiltonian()

    def calc_all(self):
        """
        Calculate the ground state, first excited state, and their properties.
        Returns:
        tuple: Ground state energy, ground state vector, first excited state energy, first excited state vector,
               density matrix of the ground state, total energy, total charge,
               expectation values of Z and XX operators.
        """
        self.E0, gs0, self.E1, ex1 = self._compute_lowest_states()

        self.gs0, self.ex1 = Statevector(gs0), Statevector(ex1)

        # Compute density matrices
        self.gs_rho = NumericalTFIM._compute_density_matrix(self.gs0)
        self.ex1_rho = NumericalTFIM._compute_density_matrix(self.ex1)

        self.bob_energy, self.bob_charge = self._compute_bob_gs_energy_and_charge()
        self.theta_E1, self.theta_E2, self.theta_q1, self.theta_q2 = self._compute_optimal_rotation_angles()

    # Hamiltonian Construction for TFIM
    def _build_tfim_hamiltonian(self):
        H = csc_matrix((2**self.N, 2**self.N), dtype=complex)
        for i in range(1, self.N):
            term = 1
            for j in range(self.N):
                term = kron(term, TFIMCalculator.X if j == i or j == 0 else TFIMCalculator.I)
            H += self.J * term

        for i in range(self.N):
            term = 1
            for j in range(self.N):
                term = kron(term, TFIMCalculator.Z if j == i else TFIMCalculator.I)
            H += self.h * term

        return H

    # Ground State and First Excited State Calculation
    def _compute_lowest_states(self):
        eigenvalues, eigenvectors = eigsh(self.H, k=2, which='SA')
        idx = np.argsort(eigenvalues)
        eigenvalues, eigenvectors = eigenvalues[idx], eigenvectors[:, idx]
        return eigenvalues[0], eigenvectors[:, 0], eigenvalues[1], eigenvectors[:, 1]

    # Density Matrix Calculation
    def _compute_density_matrix(state):
        return DensityMatrix(state)

    # Helper function for multi-site operators like X_i Z_j or X_i X_j Z_k
    def _get_multi_site_operator(ops_tuple_list, N):
        # TODO: Understand if and why this should be `idx -> N-1-idx`
        op_tuple_list = [(TFIMCalculator.pauli_ops[char], N - 1 - idx) for char, idx in ops_tuple_list]

        # Starting from identity operator on all sites
        op_list = [TFIMCalculator.pauli_ops['I']] * N

        for op, site in op_tuple_list:
            op_list[site] = op_list[site] @ op

        full_operator = op_list[0]
        for i_op in range(1, N):
            full_operator = kron(full_operator, op_list[i_op], format="csc")

        return full_operator

    # Helper to compute expectation value <gs|Op|gs>
    def _compute_expectation_value(op_matrix, gs):
        gs_col_sparse = csc_matrix(gs.data.reshape(-1, 1))
        if not isinstance(op_matrix, csc_matrix):
            op_matrix = csc_matrix(op_matrix)
        val = gs_col_sparse.conj().T @ op_matrix @ gs_col_sparse
        return val[0,0].real

    # Optimal Rotation Angles for Energy and Charge
    def _compute_optimal_rotation_angles(self):
        """
        Computes optimal rotation angles for general N.
        For energy, Bob's local energy is P_B = h*Z_{N-1} + J*X_{N-2}X_{N-1}.
        For charge, Bob's local charge is Q_B = (I+Z_{N-1})/2.
        """
        if self.N < 2:
            if self.N == 1 and self.J != 0:
                print(f"Warning: For N=1, Bob's energy P_B=hZ_0. JX_{self.N-2}X_{self.N-1} term is ignored. Recalculating E1,E2 for P_B=hZ_0.")
            elif self.N < 1:
                print(f"Warning: N={self.N} is not supported for these angle calculations. Returning zeros.")
                return 0.0, 0.0, 0.0, 0.0
            # For N=1, the J term is zero. Formulas for E1, E2 simplify.
            # Let's handle N=1 by effectively setting J_coupling to 0 for P_B construction.
            # Or, the calling code should be mindful. For now, we assume N>=2 for the J term.
            # If N=1, X_{N-2} is not defined. We'll proceed assuming N>=2 where X_{N-2} is distinct from X_{N-1} unless N=2.

        alice_site = utils.get_alice_idx(self.N)
        bob_site = utils.get_bob_idx(self.N)

        op_X0_Xbob = NumericalTFIM._get_multi_site_operator([('X', alice_site), ('X', bob_site)], self.N)
        op_Zbob = TFIMCalculator._get_pauli_operator_on_site('Z', bob_site, self.N)

        Zbob_exp = NumericalTFIM._compute_expectation_value(op_Zbob, self.gs0)
        X0_Xbob_exp = NumericalTFIM._compute_expectation_value(op_X0_Xbob, self.gs0)

        num_theta_E1 = self.h * X0_Xbob_exp - self.J * Zbob_exp
        den_theta_E1 = self.h * Zbob_exp + self.J * X0_Xbob_exp
        theta_E1 = 0.5 * np.arctan(num_theta_E1 / den_theta_E1)

        num_theta_q1 = X0_Xbob_exp
        den_theta_q1 = Zbob_exp
        theta_q1 = 0.5 * np.arctan(num_theta_q1 / den_theta_q1)

        # FIXME: Complete for other bases
        theta_E2, theta_q2 = 0.0, 0.0

        return theta_E1, theta_E2, theta_q1, theta_q2

    # Bob's Energy and Charge Expectation Calculation

    def _compute_bob_gs_energy_and_charge(self):
        gs = csc_matrix(self.gs0.data.reshape(-1, 1))

        alice_site = utils.get_alice_idx(self.N)
        bob_site = utils.get_bob_idx(self.N)

        H_b = (self.h * TFIMCalculator._get_pauli_operator_on_site('Z', bob_site, self.N) +
               self.J * NumericalTFIM._get_multi_site_operator([('X', alice_site), ('X', bob_site)], self.N))
        Q_b = kron((TFIMCalculator.I + TFIMCalculator.Z) / 2, eye(2**(self.N-1)))

        energy_bob = (gs.getH() @ (H_b @ gs)).toarray().real.item()
        charge_bob = (gs.getH() @ (Q_b @ gs)).toarray().real.item()

        return energy_bob, charge_bob
