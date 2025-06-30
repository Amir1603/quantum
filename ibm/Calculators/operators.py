from scipy.sparse.linalg import eigsh
from scipy.sparse import kron, csc_matrix
import numpy as np
import utils


class Operator:
    # Pauli Matrices
    I = csc_matrix(np.array([[1, 0], [0, 1]], dtype=complex))
    X = csc_matrix(np.array([[0, 1], [1, 0]], dtype=complex))
    Y = csc_matrix(np.array([[0, -1j], [1j, 0]], dtype=complex))
    Z = csc_matrix(np.array([[1, 0], [0, -1]], dtype=complex))
    pauli_ops = {'I': I, 'X': X, 'Y': Y, 'Z': Z}

    @staticmethod
    def get_nI(N):
        """Returns the identity operator for N qubits."""
        return Operator.I if N == 0 else kron(Operator.get_nI(N-1), Operator.I, format="csc")

    @staticmethod
    def get_Xi(N, i):
        if N == 0 and N == i:
            return Operator.X
        elif N == 0:
            return Operator.I
        elif N == i:
            return kron(Operator.get_Xi(N-1, i), Operator.X, format="csc")
        else:
            return kron(Operator.get_Xi(N-1, i), Operator.I, format="csc")

    @staticmethod
    def get_Yi(N, i):
        if N == 0 and N == i:
            return Operator.Y
        elif N == 0:
            return Operator.I
        elif N == i:
            return kron(Operator.get_Yi(N-1, i), Operator.Y, format="csc")
        else:
            return kron(Operator.get_Yi(N-1, i), Operator.I, format="csc")

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
        self.gs_expectation = np.trace(gs_dm @ self.matrix)
        self.matrix -= self.gs_expectation * Operator.get_nI(self.N)

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

        if self.alice_base == utils.AliceBase.X:
            sigma_A = Operator.get_Xi(self.N, utils.get_alice_idx(self.N))
            sigma_B = Operator.get_Yi(self.N, utils.get_bob_idx(self.N))
        elif self.alice_base == utils.AliceBase.Y:
            sigma_A = Operator.get_Yi(self.N, utils.get_alice_idx(self.N))
            sigma_B = Operator.get_Xi(self.N, utils.get_bob_idx(self.N))
        else:
            raise ValueError("Invalid Alice base. Use 'X' or 'Y'.")

        sigma_B_dot = 1j * (self.matrix @ sigma_B - sigma_B @ self.matrix)

        self.eta = np.trace(gs_dm @ sigma_A @ sigma_B_dot).real
        self.xi = np.trace(gs_dm @ sigma_B @ self.matrix @ sigma_B).real

    def calc_optimal_angle(self):
        self.theta = 0.5 * np.arctan2(-self.eta, self.xi)

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

class nn_H(H):
    def __init__(self, h, J, N):
        super().__init__(h, J, N)

    def _build_matrix(self):
        mat = csc_matrix((2**(self.N+1), 2**(self.N+1)), dtype=complex)

        for i in range(1, self.N+1):
            term = 1
            for j in range(self.N+1):
                term = kron(term, Operator.X if j == i or j == i-1 else Operator.I)
            mat += self.J * term

        for i in range(self.N+1):
            term = 1
            for j in range(self.N+1):
                term = kron(term, Operator.Z if j == i else Operator.I)
            mat += self.h * term

        return mat

class alice_H(H):
    def __init__(self, h, J, N):
        super().__init__(h, J, N)

    def _build_matrix(self):
        mat = csc_matrix((2**(self.N+1), 2**(self.N+1)), dtype=complex)

        for i in range(1, self.N+1):
            term = 1
            for j in range(self.N+1):
                term = kron(term, Operator.X if j == i or j == 0 else Operator.I)
            mat += self.J * term

        for i in range(self.N+1):
            term = 1
            for j in range(self.N+1):
                term = kron(term, Operator.Z if j == i else Operator.I)
            mat += self.h * term

        return mat

class HB(BobOperator):
    def __init__(self, h, J, N, alice_base):
        super().__init__(h, J, N, alice_base)

class nn_HB(HB):
    def __init__(self, h, J, N, alice_base):
        super().__init__(h, J, N, alice_base)

    def _build_matrix(self):
        mat = csc_matrix((2**(self.N+1), 2**(self.N+1)), dtype=complex)

        z_term = 1
        x_term = 1
        for i in range(self.N+1):
            z_term = kron(z_term, Operator.Z if i == self.N else Operator.I)
            x_term = kron(x_term, Operator.X if i == self.N or i == self.N-1 else Operator.I)

        mat += self.h * z_term + self.J * x_term

        return mat

class alice_HB(HB):
    def __init__(self, h, J, N, alice_base):
        super().__init__(h, J, N, alice_base)

    def _build_matrix(self):
        mat = csc_matrix((2**(self.N+1), 2**(self.N+1)), dtype=complex)

        x_term = 1
        z_term = 1

        for i in range(self.N+1):
            z_term = kron(z_term, Operator.Z if i == self.N else Operator.I)
            x_term = kron(x_term, Operator.X if i == self.N or i == 0 else Operator.I)

        mat += self.h * z_term + self.J * x_term

        return mat

class QB(BobOperator):
    def __init__(self, h, J, N, alice_base):
        super().__init__(h, J, N, alice_base)

    def _build_matrix(self):
        mat = csc_matrix((2**(self.N+1), 2**(self.N+1)), dtype=complex)

        i_term = 1
        z_term = 1

        for i in range(self.N+1):
            i_term = kron(i_term, Operator.I)
            z_term = kron(z_term, Operator.Z if i == self.N else Operator.I)

        mat += 0.5*(i_term + z_term)

        return mat
