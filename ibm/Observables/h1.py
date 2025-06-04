from conf import Conf
from .energy_base import EnergyBase
from Calculators.tfim_calculator import TFIMCalculator
import utils

class H1_B(EnergyBase):
    """Observable for local energy term h*Z."""
    def __init__(self, user_idx: int, conf: Conf, calc: TFIMCalculator):
        super().__init__(name=f"H1_{user_idx}", user_idx=user_idx, conf=conf, calc=calc)

    def get_bob_measurement_basis(self):
        """Indicates the runner needs to measure Z directly."""
        return "Z"

    def get_value(self, bitstring: str):
        """Calculates eigenvalue of Z (+1 or -1) from measurement outcome."""
        # Get index for Bob's Z2 measurement result (should be 1 based on utils)
        z_meas_bit = utils.get_bit_from_counts(bitstring, self.user_idx, self.N+1)
        z_eigenvalue = 1.0 if z_meas_bit == '0' else -1.0

        return z_eigenvalue

    def description(self):
        return f"h*Z_{self.user_idx} (local Z term)"
