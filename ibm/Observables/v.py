from conf import Conf
import utils
from .energy_base import EnergyBase
from Calculators.tfim_calculator import TFIMCalculator

class V_B(EnergyBase):
    """
    Observable for the interaction energy term X*X at Bob's site.
    Returns eigenvalue (+/-1).
    """
    def __init__(self, conf: Conf, calc: TFIMCalculator):
        super().__init__(name="V_B", conf=conf, calc=calc)

    def get_bob_measurement_basis(self):
        return "X"

    def get_bob_neighbour_measurement_basis(self):
        if self.N == 2:
            # For N=2, Bob's neghbour is Alice's site,
            # so no special treatment or measurement should be done.
            return None
        else:
            return "X"

    def get_value(self, bitstring: str):
        bob_idx = utils.get_bob_idx(self.N)
        bob_neighbor_idx = utils.get_bob_neighbor_idx(self.N)

        bob_bit = utils.get_bit_from_counts(bitstring, bob_idx, self.N)
        bob_neighbour_bit = utils.get_bit_from_counts(bitstring, bob_neighbor_idx, self.N)

        bob_neighbour_val = 1 if bob_neighbour_bit == '0' else -1
        bob_val = 1 if bob_bit == '0' else -1

        return bob_neighbour_val * bob_val

    def description(self):
        bob_idx = utils.get_bob_idx(self.N)
        bobs_beighbor_idx = utils.get_bob_neighbor_idx(self.N)

        return f"Measure X{bobs_beighbor_idx}*X{bob_idx} for N={self.N}"
