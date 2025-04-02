from .qkd_base_n3 import QKDBaseN3
from conf import Conf
import utils

class H1_N3(QKDBaseN3):
    """Observable to measure Z2 term for N=3 QKD protocol. Analogous to H1_B for N=2."""
    def __init__(self, conf: Conf, alice_basis: str):
        super().__init__(name_suffix="h1", conf=conf, alice_basis=alice_basis) # name: qkd_h1_n3_alice_x/y

    def get_bob_measurement_basis(self):
        """Indicates the runner needs to measure Z2 directly."""
        return "Z2" # String identifier

    def get_value(self, bitstring: str):
        """Calculates eigenvalue of Z2 (+1 or -1) from measurement outcome."""
        # EXPECT 3 classical bits based on runner standardization for N=3
        num_clbits = 3
        try:
            # Get index for Bob's Z2 measurement result (should be 1 based on utils)
            bob_creg = utils.get_counts_bob_creg_idx(self.N)
            z2_meas_bit = utils.get_bit_from_counts(bitstring, bob_creg, num_clbits)
            z2_eigenvalue = 1.0 if z2_meas_bit == '0' else -1.0
            return z2_eigenvalue
        except IndexError as e:
            # Catch potential errors from get_bit_from_counts
            print(f"Error in {self.name}.get_value: Bitstring '{bitstring}', {e}")
            # Re-raise or return default? Re-raising might be better for debugging.
            raise e # Or return 0.0

    def description(self):
        return f"Measure Z2 for N=3 QKD (Alice Basis: {self.alice_basis}, J={self.k})"
