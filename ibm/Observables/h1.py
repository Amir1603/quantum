from conf import Conf
from constants import *
import numpy as np
from qiskit.quantum_info import SparsePauliOp
from .energy import Energy


class H1(Energy):
    def __init__(self, conf: Conf):
        super().__init__("h1",
                         SparsePauliOp.from_list([
                             ("ZI", conf.h),
                             ("II", conf.h**2 / np.sqrt(conf.h**2 + conf.k**2))
                            ]),
                         conf.h,
                         conf.k)

    def get_bob_measurement_basis(self):
        return "Z"

    def get_value(self, bitstring: str):
        if bitstring[COUNTS_BOB_QUBIT_IDX] == '0':
            return 1
        else:
            return -1

    def description(self):
        return "Z (H1)"