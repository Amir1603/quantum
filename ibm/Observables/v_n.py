from .energy_n import Energy_N
from Calculators.tfim_calculator import TFIMCalculator
from conf import Conf
import utils

class V_N(Energy_N):
    """
    Observable to measure X_{N-2}*X_{N-1} term for arbitrary QKD protocol.
    Note: Returns eigenvalue (+/-1). Factor J applied during derived calculation.
    """
    def __init__(self, conf: Conf, alice_basis: str, calc: TFIMCalculator):
        super().__init__(name_suffix="v", conf=conf, alice_basis=alice_basis, calc=calc)

    def get_bob_measurement_basis(self):
        """Indicates the runner needs to measure X_{N-2}*X_{N-1} (requires H gates)."""
        return f"X{self.N-2}X{self.N-1}"

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
        return f"Measure X{self.N-2}*X{self.N-1} for arbitrary N QKD (Alice Basis: {self.alice_basis}, J={self.J})"
