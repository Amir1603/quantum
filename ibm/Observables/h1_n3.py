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
        # Assumes bitstring format c...c1c0 based on runner's measurement order.
        # Need number of classical bits used in the circuit for this measurement.
        num_clbits = 2 # Alice (c0), Z2 (c1) for this observable's circuit
        try:
            bob_creg = utils.get_counts_bob_creg_idx(self.N) # Expect index 1
            z2_meas_bit = utils.get_bit_from_counts(bitstring, bob_creg, num_clbits)
            z2_eigenvalue = 1.0 if z2_meas_bit == '0' else -1.0
            return z2_eigenvalue
        except IndexError as e:
            print(f"Error in {self.name}.get_value: Bitstring '{bitstring}', {e}")
            return 0.0 # Or raise error

    def description(self):
        return f"Measure Z2 for N=3 QKD (Alice Basis: {self.alice_basis}, J={self.J_param})"
