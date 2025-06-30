from scipy.sparse import kron
from qiskit.quantum_info import Statevector, DensityMatrix
from .tfim_calculator import TFIMCalculator
from .operators import BobOperator, H

class NumericalTFIM(TFIMCalculator):
    def __init__(self, H: H, ops: list[BobOperator]):
        super().__init__(H.N, H.J, H.h)
        self.H = H
        self.ops = ops

    def calc_all(self):
        """
        Calculate the ground state, first excited state, and their properties.
        Returns:
        tuple: Ground state energy, ground state vector, first excited state energy, first excited state vector,
               density matrix of the ground state, total energy, total charge,
               expectation values of Z and XX operators.
        """
        self.E0, gs0, self.E1, ex1 = self.H.get_lowest_states()
        self.gs0, self.ex1 = Statevector(gs0), Statevector(ex1)

        # Compute density matrices
        self.gs_rho = NumericalTFIM._compute_density_matrix(self.gs0)
        self.ex1_rho = NumericalTFIM._compute_density_matrix(self.ex1)

        for op in self.ops:
            op.shift(self.gs_rho.data)
            op.calc_eta_xi(self.gs_rho.data)
            op.calc_optimal_angle()
            op.calc_teleported_values()

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

    def _build_tfim_hamiltonian(self):
        raise NotImplementedError("This method should be implemented in subclasses.")