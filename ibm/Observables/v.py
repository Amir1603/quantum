from conf import Conf
from constants import *
import numpy as np
from qiskit.quantum_info import SparsePauliOp
from .energy import Energy


class V(Energy):
    def __init__(self, conf: Conf):
        super().__init__("v",
                         SparsePauliOp.from_list([
                             ("XX", 2 * conf.k),
                             ("II", 2 * conf.k**2 / np.sqrt(conf.h**2 + conf.k**2))
                             ]),
                         conf.h,
                         conf.k)

    def get_bob_measurement_basis(self):
        return "X"

    def get_value(self, bitstring: str):
        if bitstring in ('11', '00'):
            return 1
        else:
            return -1

    def description(self):
        return "XX (V)"