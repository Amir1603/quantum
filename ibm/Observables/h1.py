from conf import Conf
from .energy_n2 import Energy_N2
import utils

class H1_B(Energy_N2):
    """Observable for Bob's local energy term h*Z1."""
    def __init__(self, conf: Conf):
        super().__init__("h1", conf)

    def get_bob_measurement_basis(self):
        return "Z"

    def get_value(self, bitstring: str):
        bob_bit = bitstring[utils.get_counts_bob_qubit_idx(self.N)]
        if bob_bit == '0':
            return 1 # Z eigenvalue for |0>
        else:
            return -1 # Z eigenvalue for |1>

    def description(self):
        return "h*Z_1 (Bob's local Z term)"
