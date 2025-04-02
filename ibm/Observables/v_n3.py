from .qkd_base_n3 import QKDBaseN3
from conf import Conf
import utils

class V_N3(QKDBaseN3):
    """
    Observable to measure X1*X2 term for N=3 QKD protocol. Analogous to V_AB for N=2.
    Note: Returns eigenvalue (+/-1). Factor J applied during derived calculation.
    """
    def __init__(self, conf: Conf, alice_basis: str):
        super().__init__(name_suffix="v", conf=conf, alice_basis=alice_basis) # name: qkd_v_n3_alice_x/y

    def get_bob_measurement_basis(self):
        """Indicates the runner needs to measure X1*X2 (requires H gates)."""
        return "X1X2" # String identifier

    def get_value(self, bitstring: str):
        """
        Calculates eigenvalue of X1*X2 (+1 or -1) from Z1, Z2 measurement outcomes...
        """
        # Ensure this is 3, matching the runner for N=3
        num_clbits = 3
        try:
            intermed_creg = utils.get_counts_intermediate_creg_idx(self.N) # Expect index 2
            bob_creg = utils.get_counts_bob_creg_idx(self.N) # Expect index 1

            # Ensure get_bit_from_counts is used correctly
            z1_meas_bit = utils.get_bit_from_counts(bitstring, intermed_creg, num_clbits)
            z2_meas_bit = utils.get_bit_from_counts(bitstring, bob_creg, num_clbits)

            z1_eigenvalue = 1.0 if z1_meas_bit == '0' else -1.0
            z2_eigenvalue = 1.0 if z2_meas_bit == '0' else -1.0

            return z1_eigenvalue * z2_eigenvalue
        except IndexError as e:
            print(f"Error in {self.name}.get_value: Bitstring '{bitstring}', {e}")
            raise e # Or return 0.0

    def description(self):
        return f"Measure X1*X2 for N=3 QKD (Alice Basis: {self.alice_basis}, J={self.k})"
