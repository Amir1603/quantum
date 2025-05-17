from conf import Conf
from .energy_base import EnergyBase
from Calculators.tfim_calculator import TFIMCalculator
import utils

class H1_B(EnergyBase):
    """Observable for Bob's local energy term h*Z."""
    def __init__(self, conf: Conf, calc: TFIMCalculator):
        super().__init__(name="H1_B", conf=conf, calc=calc)

    def get_bob_measurement_basis(self):
        """Indicates the runner needs to measure Z at Bob's site directly."""
        bob_idx = utils.get_bob_idx(self.N)
        return f"Z{bob_idx}"

    def get_value(self, bitstring: str):
        """Calculates eigenvalue of Z at Bob's site (+1 or -1) from measurement outcome."""
        # Get index for Bob's Z2 measurement result (should be 1 based on utils)
        bob_creg = utils.get_bob_idx(self.N)
        z_meas_bit = utils.get_bit_from_counts(bitstring, bob_creg, self.N)
        z_eigenvalue = 1.0 if z_meas_bit == '0' else -1.0

        return z_eigenvalue

    def description(self):
        bob_idx = utils.get_bob_idx(self.N)
        return f"h*Z_{bob_idx} (Bob's local Z term)"
