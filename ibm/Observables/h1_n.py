from .energy_n import Energy_N
from conf import Conf
import utils

class H1_N(Energy_N):
    """Observable to measure Z_{N-1} term for arbitrary N QKD protocol."""
    def __init__(self, conf: Conf, alice_basis: str):
        super().__init__(name_suffix="h1", conf=conf, alice_basis=alice_basis)

    def get_bob_measurement_basis(self):
        """Indicates the runner needs to measure Z_{N-1} directly."""
        return f"Z{self.N-1}" # String identifier

    def get_value(self, bitstring: str):
        """Calculates eigenvalue of Z_{N-1} (+1 or -1) from measurement outcome."""
        try:
            # Get index for Bob's Z2 measurement result (should be 1 based on utils)
            bob_creg = utils.get_counts_bob_creg_idx(self.N)
            z_meas_bit = utils.get_bit_from_counts(bitstring, bob_creg, self.N)
            z_eigenvalue = 1.0 if z_meas_bit == '0' else -1.0
            return z_eigenvalue
        except IndexError as e:
            # Catch potential errors from get_bit_from_counts
            print(f"Error in {self.name}.get_value: Bitstring '{bitstring}', {e}")
            # Re-raise or return default? Re-raising might be better for debugging.
            raise e # Or return 0.0
