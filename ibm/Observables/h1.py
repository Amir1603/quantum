from conf import Conf
from .energy_n2 import Energy_N2
from Calculators.tfim_calculator import TFIMCalculator
import utils

class H1_B(Energy_N2):
    """Observable for Bob's local energy term h*Z1."""
    def __init__(self, conf: Conf, calc: TFIMCalculator):
        super().__init__("h1", conf, calc)

    def get_bob_measurement_basis(self):
        return "Z"

    def get_value(self, bitstring: str):
        bob_bit = utils.get_bit_from_counts(bitstring, utils.get_bob_idx(self.N), self.N)

        if bob_bit == '0':
            return 1 # Z eigenvalue for |0>
        else:
            return -1 # Z eigenvalue for |1>

    def description(self):
        return "h*Z_1 (Bob's local Z term)"
