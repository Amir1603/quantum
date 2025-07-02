from .operator import Operator
from scipy.sparse import csc_matrix
import numpy as np
import utils

class BobOperator(Operator):
    def __init__(self, h, J, N, alice_base: str):
        super().__init__(h, J, N)

        self.alice_base = alice_base

        self.eta = None
        self.xi = None
        self.theta = None
        self.teleported_values = None

    def calc_eta_xi(self, gs_dm: np.ndarray):
        sigma_A = None
        sigma_B = None

        alice_idx = utils.get_alice_idx(self.N)
        bob_idx = utils.get_bob_idx(self.N)

        if self.alice_base == utils.AliceBase.X:
            sigma_A = utils.get_pauli_operator_on_site('X', alice_idx, self.N)
            sigma_B = utils.get_pauli_operator_on_site('Y', bob_idx, self.N)
        elif self.alice_base == utils.AliceBase.Y:
            sigma_A = utils.get_pauli_operator_on_site('Y', alice_idx, self.N)
            sigma_B = utils.get_pauli_operator_on_site('X', bob_idx, self.N)
        else:
            raise ValueError("Invalid Alice base. Use 'X' or 'Y'.")

        sigma_B_dot = 1j * (self.matrix @ sigma_B - sigma_B @ self.matrix)
        self.eta = np.trace(gs_dm @ sigma_A @ sigma_B_dot).real
        self.xi = np.trace(gs_dm @ sigma_B @ self.matrix @ sigma_B).real

    def calc_optimal_angle(self):
        self.theta = 0.5 * np.arctan2(self.eta, self.xi)

    def calc_teleported_values(self):
        As = [False, True]

        numerators = {a: self.xi**2 + (-1)**a * self.eta**2 for a in As}
        den = np.sqrt(self.xi**2 + self.eta**2)

        if den == 0:
            self.teleported_values = {
                a: 0 for a, _ in numerators.items()
            }
        else:
            self.teleported_values = {
                a: 0.5*(self.xi - num / den) for a, num in numerators.items()
            }

class HB(BobOperator):
    def __init__(self, h, J, N, alice_base):
        super().__init__(h, J, N, alice_base)

    def _build(self, int_site_idx: int):
        mat = csc_matrix((2**(self.N+1), 2**(self.N+1)), dtype=complex)

        bob_idx = utils.get_bob_idx(self.N)

        z_op = utils.get_pauli_operator_on_site('Z', bob_idx, self.N)
        xx_op = utils.get_multi_site_operator([('X', int_site_idx), ('X', bob_idx)], self.N)

        mat += self.h * z_op + self.J * xx_op

        return mat

class nn_HB(HB):
    def __init__(self, h, J, N, alice_base):
        super().__init__(h, J, N, alice_base)

    def _build_matrix(self):
        return self._build(utils.get_bob_neighbor_idx(self.N))

class alice_HB(HB):
    def __init__(self, h, J, N, alice_base):
        super().__init__(h, J, N, alice_base)

    def _build_matrix(self):
        return self._build(utils.get_alice_idx(self.N))

class QB(BobOperator):
    def __init__(self, h, J, N, alice_base):
        super().__init__(h, J, N, alice_base)

    def _build_matrix(self):
        mat = csc_matrix((2**(self.N+1), 2**(self.N+1)), dtype=complex)

        bob_idx = utils.get_bob_idx(self.N)

        i_op = utils.get_pauli_operator_on_site('I', bob_idx, self.N)
        z_op = utils.get_pauli_operator_on_site('Z', bob_idx, self.N)

        mat += 0.5*(i_op + z_op)

        return mat
