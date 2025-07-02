from scipy.sparse import kron
from qiskit.quantum_info import Statevector, DensityMatrix
from .tfim_calculator import TFIMCalculator
from .Operators import H, BobOperator
from conf import Conf

class NumericalTFIM(TFIMCalculator):
    def __init__(self, H: H, ops: list[BobOperator]):
        super().__init__(H.N, H.J, H.h)
        self.H = H
        self.ops = {type(o).__name__: o for o in ops}

    def calc_all(self, conf: Conf):
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

        for op in self.ops.values():
            op.shift(self.gs_rho.data)
            op.calc_eta_xi(self.gs_rho.data)
            op.calc_optimal_angle()
            op.calc_teleported_values()

        # TODO: Currently we want the errors to affect only the density matrix initialized into the
        #       quantum circuit and not to affect the calculation of the optimal rotation angle theta.
        #       When applying errors also with numerical theoretical plots, we should introduce the
        #       errors before the calculations to see how it affect the results.
        self.apply_errors(conf)

    # Density Matrix Calculation
    def _compute_density_matrix(state):
        return DensityMatrix(state)
