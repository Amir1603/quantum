from scipy.sparse import csc_matrix
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
