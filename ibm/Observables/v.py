from conf import Conf
import utils
from .energy_n2 import Energy_N2
from Calculators.tfim_calculator import TFIMCalculator

class V_AB(Energy_N2):
    """Observable for the interaction energy term J*X0X1."""
    def __init__(self, conf: Conf, calc: TFIMCalculator):
        super().__init__("v", conf, calc)

    def get_bob_measurement_basis(self):
        return "X"

    def get_value(self, bitstring: str):
        bob_bit = utils.get_bit_from_counts(bitstring, utils.get_bob_idx(self.N), self.N)
        alice_bit = utils.get_bit_from_counts(bitstring, utils.get_alice_idx(self.N), self.N)

        alice_val = 1 if alice_bit == '0' else -1
        bob_val = 1 if bob_bit == '0' else -1

        # Value is product of eigenvalues
        return alice_val * bob_val

    def description(self):
        return "J*X_0*X_1"
