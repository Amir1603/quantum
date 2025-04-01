from conf import Conf
from constants import *
import numpy as np
from qiskit.quantum_info import SparsePauliOp
from .energy import Energy


class H1_B(Energy):
    """Observable for Bob's local energy term h*Z1."""
    def __init__(self, conf: Conf):
        super().__init__("h1", conf.h, conf.k)

    def get_bob_measurement_basis(self):
        return "Z"

    def get_value(self, bitstring: str):
        bob_bit = bitstring[COUNTS_BOB_QUBIT_IDX]
        if bob_bit == '0':
            return 1 # Z eigenvalue for |0>
        else:
            return -1 # Z eigenvalue for |1>

    def description(self):
        return "h*Z_1 (Bob's local Z term)"
