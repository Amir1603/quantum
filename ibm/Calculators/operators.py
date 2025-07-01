from scipy.sparse.linalg import eigsh
from scipy.sparse import kron, csc_matrix
import numpy as np
import utils


class Operator:
    def __init__(self, h, J, N):
        self.h = h
        self.J = J
        self.N = N

        self.matrix = self._build_matrix()

        self.gs_expectation = None

    def _build_matrix(self) -> csc_matrix:
        raise NotImplementedError("Subclasses should implement this method")

    # Shift the operator according to the gs expectation value <state|Op|state>
    def shift(self, gs_dm: np.ndarray):
        self.gs_expectation = np.trace(gs_dm @ self.matrix).real
        # The site idx is irrelevant because we want the identity operator
        I = utils.get_pauli_operator_on_site('I', 0, self.N)
        self.matrix -= self.gs_expectation * I

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

class H(Operator):
    def __init__(self, h, J, N):
        super().__init__(h, J, N)

    # Ground State and First Excited State Calculation
    def get_lowest_states(self):
        eigenvalues, eigenvectors = eigsh(self.matrix, k=2, which='SA')
        idx = np.argsort(eigenvalues)
        eigenvalues, eigenvectors = eigenvalues[idx], eigenvectors[:, idx]
        return eigenvalues[0], eigenvectors[:, 0], eigenvalues[1], eigenvectors[:, 1]

    def _build(self, interaction_idx_lambda):
        # TODO: Use get pauli op on site
        # mat = csc_matrix((2**(self.N+1), 2**(self.N+1)), dtype=complex)

        # alice_idx = utils.get_alice_idx(self.N)

        # for i in range(1, self.N+1):
        #     op = utils.get_multi_site_operator([('X', alice_idx), ('X', i)], self.N)
        #     mat += self.J * op

        # for i in range(self.N+1):
        #     op = utils.get_pauli_operator_on_site('Z', i, self.N)
        #     mat += self.h * op

        # return mat
        H = csc_matrix((2**(self.N+1), 2**(self.N+1)), dtype=complex)
        for i in range(1, self.N+1):
            term = 1
            for j in range(self.N+1):
                term = kron(term, utils.X if j == i or j == interaction_idx_lambda(i) else utils.I)
            H += self.J * term

        for i in range(self.N+1):
            term = 1
            for j in range(self.N+1):
                term = kron(term, utils.Z if j == i else utils.I)
            H += self.h * term

        return H

class nn_H(H):
    def __init__(self, h, J, N):
        super().__init__(h, J, N)

    def _build_matrix(self):
        return self._build(lambda i: i-1)

class alice_H(H):
    def __init__(self, h, J, N):
        super().__init__(h, J, N)

    def _build_matrix(self):
        return self._build(lambda _: utils.get_alice_idx(self.N))

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
