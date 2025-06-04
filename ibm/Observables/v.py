from conf import Conf
import utils
from .energy_base import EnergyBase
from Calculators.tfim_calculator import TFIMCalculator

class V_B(EnergyBase):
    """
    Observable for the interaction energy term X*X.
    Returns eigenvalue (+/-1).
    """
    def __init__(self, user_idx: int, conf: Conf, calc: TFIMCalculator):
        super().__init__(name=f"V_{user_idx}", user_idx=user_idx, conf=conf, calc=calc)

    def get_bob_measurement_basis(self):
        return "X"

    def get_value(self, bitstring: str):
        alice_idx = utils.get_alice_idx(self.N)

        users_bit = utils.get_bit_from_counts(bitstring, self.user_idx, self.N+1)
        alice_bit = utils.get_bit_from_counts(bitstring, alice_idx, self.N+1)

        alice_val = 1 if alice_bit == '0' else -1
        users_val = 1 if users_bit == '0' else -1

        return alice_val * users_val

    def description(self):
        alice_idx = utils.get_alice_idx(self.N)

        return f"Measure X{alice_idx}*X{self.user_idx} for N={self.N}"
