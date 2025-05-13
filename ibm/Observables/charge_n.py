import numpy as np
from qiskit import QuantumCircuit
from .observable import Observable
from Calculators.tfim_calculator import TFIMCalculator
from conf import Conf
import utils

class Charge_N(Observable):
    """
    Observable for Bob's local charge density (rho_B ~ (I+Z{N-1})/2) for arbitrary N,
    under the protocol optimized for energy (Alice measures X0, Bob rotates Ry based on theta).
    """
    def __init__(self, conf: Conf, apply_protocol: bool, calc: TFIMCalculator):
        self.apply_protocol = apply_protocol
        protocol_tag = '' if apply_protocol else '_no_protocol'
        # Use a distinct name
        name = f'charge_n{protocol_tag}'
        super().__init__(name, conf, calc)

    def apply_alice_measurement(self, qc: QuantumCircuit, alice_qubit_idx, alice_creg):
        """
        Alice measures X basis (H + Z measure) as required by the energy protocol context.
        """
        qc.h(alice_qubit_idx)
        qc.measure(alice_qubit_idx, alice_creg) # Measure Alice (q0) into classical bit 0

    def apply_bob_operation(self, qc: QuantumCircuit, bob_qubit_idx, alice_creg, xor_alice_res: int):
        """
        Bob's conditional Ry rotation on site N-1, based on Alice's X measurement (c0).
        Uses the energy-optimal theta.
        """
        if self.apply_protocol:
            if self.theta is None:
                raise ValueError(f"Theta is None for observable {self.name}. Cannot apply Bob's operation.")

            protocol_theta = self.theta
            # Apply Ry based on Alice's outcome b (in alice_creg) XOR xor_alice_res
            # We want rotation exp(-i * theta * (-1)^b_eff * Y_{N-1})
            # Qiskit Ry(a) is exp(-i * a/2 * Y) -> a = 2 * theta * (-1)^b_eff
            target_b_0 = 0 ^ xor_alice_res
            target_b_1 = 1 ^ xor_alice_res
            qiskit_angle_if_0 = 2 * protocol_theta  # Angle for b_eff=0
            qiskit_angle_if_1 = -2 * protocol_theta # Angle for b_eff=1

            with qc.if_test((alice_creg, target_b_0)):
                 qc.ry(qiskit_angle_if_0, bob_qubit_idx)
            with qc.if_test((alice_creg, target_b_1)):
                 qc.ry(qiskit_angle_if_1, bob_qubit_idx)

    def get_bob_measurement_basis(self):
        """
        Bob measures charge density Z{N-1}. Requires Z basis.
        """
        return f"Z{self.N-1}"

    def get_value(self, bitstring: str):
        """
        Extracts the eigenvalue for Bob's charge density operator (I + Z_{N-1}) / 2.
        Returns 1.0 if Z_{N-1}=+1 (measured '0'), 0.0 if Z_{N-1}=-1 (measured '1').
        """
        try:
            # Bob's Z2 measurement is expected in classical register 1 (utils.get_counts_bob_creg_idx)
            bob_creg_index = utils.get_counts_bob_creg_idx(self.N)
            bob_measurement_bit = utils.get_bit_from_counts(bitstring, bob_creg_index, self.N)

            if bob_measurement_bit == '0':
                return 1.0 # Z{N-1} eigenvalue +1 -> charge density eigenvalue 1
            else:
                return 0.0 # Z{N-1} eigenvalue -1 -> charge density eigenvalue 0
        except IndexError as e:
            print(f"Error in {self.name}.get_value: Bitstring '{bitstring}', {e}")
            raise e

    def get_theoretical_gs_expectation_value(self):
        return self._calc.bob_charge

    def description(self):
        protocol_state = "Protocol ON" if self.apply_protocol else "Protocol OFF"
        return f"Bob's Charge Density (I+Z{self.N-1})/2 ({protocol_state})"