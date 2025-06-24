from conf import Conf
import utils
from .energy_base import EnergyBase
from Calculators.tfim_calculator import TFIMCalculator

class V_B(EnergyBase):
    """
    Observable for the interaction energy term X*X at Bob's site.
    Returns eigenvalue (+/-1).
    """
    def __init__(self, conf: Conf, calc: TFIMCalculator, sys: utils.System):
        super().__init__(name="V_B", conf=conf, calc=calc)
        self.sys = sys

    def get_bob_measurement_basis(self):
        return "X"

    def get_value(self, bitstring: str):
        bob_idx = utils.get_bob_idx(self.N)

        interaction_site = utils.get_alice_idx(self.N) \
                            if self.sys == utils.System.AliceInteraction \
                            else utils.get_bob_neighbor_idx(self.N)

        bob_bit = utils.get_bit_from_counts(bitstring, bob_idx, self.N+1)
        interaction_bit = utils.get_bit_from_counts(bitstring, interaction_site, self.N+1)

        interaction_val = 1 if interaction_bit == '0' else -1
        bob_val = 1 if bob_bit == '0' else -1

        return interaction_val * bob_val

    def description(self):
        bob_idx = utils.get_bob_idx(self.N)
        interaction_site = utils.get_alice_idx(self.N) \
                            if self.sys == utils.System.AliceInteraction \
                            else utils.get_bob_neighbor_idx(self.N)


        return f"Measure X{interaction_site}*X{bob_idx} for N={self.N}"
