from conf import Conf
import utils
from .energy_n2 import Energy_N2
from Calculators.tfim_calculator import TFIMCalculator

class V_AB(Energy_N2):
    """Observable for the interaction energy term 2k*X0X1."""
    def __init__(self, conf: Conf, calc: TFIMCalculator):
        super().__init__("v", conf, calc)

    def get_bob_measurement_basis(self):
        return "X"

    def get_value(self, bitstring: str):
        bob_bit = bitstring[utils.get_counts_bob_qubit_idx(self.N)]
        alice_bit = bitstring[utils.get_counts_alice_qubit_idx(self.N)]

        alice_val = 1 if alice_bit == '0' else -1
        bob_val = 1 if bob_bit == '0' else -1

        # Value is product of eigenvalues
        return alice_val * bob_val

    def description(self):
        return "2k*X_0*X_1"
