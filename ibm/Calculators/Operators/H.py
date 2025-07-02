from .operator import Operator
import numpy as np
from scipy.sparse.linalg import eigsh
from scipy.sparse import kron, csc_matrix
import utils

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
