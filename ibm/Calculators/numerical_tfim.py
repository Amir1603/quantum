import numpy as np
from scipy.sparse import kron, csc_matrix
from scipy.sparse.linalg import eigsh
import utils
from qiskit.quantum_info import Statevector, DensityMatrix
from .tfim_calculator import TFIMCalculator

class ExpectationValues:
    def __init__(self):
        self.X0 = None
        self.Y0 = None
        self.Xbob = None
        self.Zbob = None
        self.Ybob = None
        self.X0_Xbob = None
        self.Y0_Ybob = None
        self.X0_Zbob = None
        self.Y0_Zbob = None
        self.Xbobn_Zbob = None
        self.X0_Xbobn_Zbob = None
        self.X0_Xbobn_Xbob = None
        self.Y0_Xbobn_Xbob = None

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

        self._raw_exp_vals = self.get_expectation_values()

        self.bob_energy, self.bob_charge = self._compute_bob_gs_energy_and_charge()
        self.theta_E1, self.theta_q1 = self._compute_optimal_rotation_angles()

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
        # We reverse the indices because the kron product builds operators from left to right,
        # which means the leftmost operator acts on the most significant qubit.
        op_tuple_list = [(TFIMCalculator.pauli_ops[char], N - idx) for char, idx in ops_tuple_list]

        # Starting from identity operator on all sites
        op_list = [TFIMCalculator.pauli_ops['I']] * (N+1)

        for op, site in op_tuple_list:
            op_list[site] = op_list[site] @ op

        full_operator = op_list[0]
        for i_op in range(1, N+1):
            full_operator = kron(full_operator, op_list[i_op], format="csc")

        return full_operator

    # Helper to compute expectation value <state|Op|state>
    def _compute_expectation_value(op_matrix, state):
        state_col_sparse = csc_matrix(state.data.reshape(-1, 1))
        if not isinstance(op_matrix, csc_matrix):
            op_matrix = csc_matrix(op_matrix)
        val = state_col_sparse.conj().T @ op_matrix @ state_col_sparse
        return val[0,0].real

    def get_expectation_values(self):
        alice_site = utils.get_alice_idx(self.N)
        bob_site = utils.get_bob_idx(self.N)

        # Create Pauli operators
        op_X0 = TFIMCalculator._get_pauli_operator_on_site('X', alice_site, self.N)
        op_Y0 = TFIMCalculator._get_pauli_operator_on_site('Y', alice_site, self.N)
        op_Xbob = TFIMCalculator._get_pauli_operator_on_site('X', bob_site, self.N)
        op_Ybob = TFIMCalculator._get_pauli_operator_on_site('Y', bob_site, self.N)

        op_X0_Xbob = NumericalTFIM._get_multi_site_operator([('X', alice_site), ('X', bob_site)], self.N)
        op_Y0_Ybob = NumericalTFIM._get_multi_site_operator([('Y', alice_site), ('Y', bob_site)], self.N)
        op_Zbob = TFIMCalculator._get_pauli_operator_on_site('Z', bob_site, self.N)
        op_X0_Zbob = NumericalTFIM._get_multi_site_operator([('X', alice_site), ('Z', bob_site)], self.N)
        op_Y0_Zbob = NumericalTFIM._get_multi_site_operator([('Y', alice_site), ('Z', bob_site)], self.N)
        op_Xbobn_Zbob = NumericalTFIM._get_multi_site_operator([('X', bob_site-1), ('Z', bob_site)], self.N)

        op_X0_Xbobn_Zbob = NumericalTFIM._get_multi_site_operator([('X', alice_site), ('X', bob_site-1), ('Z', bob_site)], self.N)
        op_X0_Xbobn_Xbob = NumericalTFIM._get_multi_site_operator([('X', alice_site), ('X', bob_site-1), ('X', bob_site)], self.N)
        op_Y0_Xbobn_Xbob = NumericalTFIM._get_multi_site_operator([('Y', alice_site), ('X', bob_site-1), ('X', bob_site)], self.N)

        # Compute gs expectation values
        X0_exp = NumericalTFIM._compute_expectation_value(op_X0, self.gs0)
        Y0_exp = NumericalTFIM._compute_expectation_value(op_Y0, self.gs0)
        Xbob_exp = NumericalTFIM._compute_expectation_value(op_Xbob, self.gs0)
        Ybob_exp = NumericalTFIM._compute_expectation_value(op_Ybob, self.gs0)
        Zbob_exp = NumericalTFIM._compute_expectation_value(op_Zbob, self.gs0)
        X0_Xbob_exp = NumericalTFIM._compute_expectation_value(op_X0_Xbob, self.gs0)
        Y0_Ybob_exp = NumericalTFIM._compute_expectation_value(op_Y0_Ybob, self.gs0)
        X0_Zbob_exp = NumericalTFIM._compute_expectation_value(op_X0_Zbob, self.gs0)
        Y0_Zbob_exp = NumericalTFIM._compute_expectation_value(op_Y0_Zbob, self.gs0)
        Xbobn_Zbob_exp = NumericalTFIM._compute_expectation_value(op_Xbobn_Zbob, self.gs0)
        X0_Xbobn_Zbob_exp = NumericalTFIM._compute_expectation_value(op_X0_Xbobn_Zbob, self.gs0)
        X0_Xbobn_Xbob_exp = NumericalTFIM._compute_expectation_value(op_X0_Xbobn_Xbob, self.gs0)
        Y0_Xbobn_Xbob_exp = NumericalTFIM._compute_expectation_value(op_Y0_Xbobn_Xbob, self.gs0)

        exp = ExpectationValues()
        exp.__dict__ = {
            'X0': X0_exp,
            'Y0': Y0_exp,
            'Xbob': Xbob_exp,
            'Ybob': Ybob_exp,
            'Zbob': Zbob_exp,
            'X0_Xbob': X0_Xbob_exp,
            'Y0_Ybob': Y0_Ybob_exp,
            'X0_Zbob': X0_Zbob_exp,
            'Y0_Zbob': Y0_Zbob_exp,
            'Xbobn_Zbob': Xbobn_Zbob_exp,
            'X0_Xbobn_Zbob': X0_Xbobn_Zbob_exp,
            'X0_Xbobn_Xbob': X0_Xbobn_Xbob_exp,
            'Y0_Xbobn_Xbob': Y0_Xbobn_Xbob_exp
        }
        return exp

    def _build_tfim_hamiltonian(self):
        raise NotImplementedError("This method should be implemented in subclasses.")