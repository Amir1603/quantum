from conf import Conf
from constants import *
import numpy as np
from qiskit.quantum_info import SparsePauliOp
from .energy import Energy


class V_AB(Energy):
    """Observable for the interaction energy term 2k*X0X1."""
    def __init__(self, conf: Conf):
        super().__init__("v", conf.h, conf.k)

    def get_bob_measurement_basis(self):
        return "X"

    def get_value(self, bitstring: str):
        bob_bit = bitstring[COUNTS_BOB_QUBIT_IDX]
        alice_bit = bitstring[COUNTS_ALICE_QUBIT_IDX]

        alice_val = 1 if alice_bit == '0' else -1
        bob_val = 1 if bob_bit == '0' else -1

        # Value is product of eigenvalues
        return alice_val * bob_val

    def description(self):
        return "2k*X_0*X_1"
