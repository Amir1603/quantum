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
        bob_bit = utils.get_bit_from_counts(bitstring, utils.get_bob_idx(self.N), self.N)
        bob_neighbour_bit = utils.get_bit_from_counts(bitstring, utils.get_bob_neighbor_idx(self.N), self.N)

        bob_neighbour_val = 1 if bob_neighbour_bit == '0' else -1
        bob_val = 1 if bob_bit == '0' else -1

        # Value is product of eigenvalues
        return bob_neighbour_val * bob_val

    def get_value(self, bitstring: str):
        """
        Calculates eigenvalue of X_{N-2}*X_{N-1} (+1 or -1) from Z_{N-2}, Z_{N-1} measurement outcomes...
        """
        try:
            intermed_creg = utils.get_bob_neighbor_idx(self.N)
            bob_creg = utils.get_bob_idx(self.N)

            # Ensure get_bit_from_counts is used correctly
            z1_meas_bit = utils.get_bit_from_counts(bitstring, intermed_creg, self.N)
            z2_meas_bit = utils.get_bit_from_counts(bitstring, bob_creg, self.N)

            z1_eigenvalue = 1.0 if z1_meas_bit == '0' else -1.0
            z2_eigenvalue = 1.0 if z2_meas_bit == '0' else -1.0

            return z1_eigenvalue * z2_eigenvalue
        except IndexError as e:
            print(f"Error in {self.name}.get_value: Bitstring '{bitstring}', {e}")
            raise e # Or return 0.0

    def description(self):
        bob_idx = utils.get_bob_idx(self.N)
        bobs_beighbor_idx = utils.get_bob_neighbor_idx(self.N)

        return f"Measure X{bobs_beighbor_idx}*X{bob_idx} for N={self.N}"
