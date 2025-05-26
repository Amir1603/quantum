from qiskit import QuantumCircuit
from .observable import Observable
from Calculators.tfim_calculator import TFIMCalculator
from conf import Conf
import utils

class Charge(Observable):
    """
    Observable for Bob's local charge density (rho_B ~ (I+Z)/2) for arbitrary N,
    under the protocol optimized for energy (Alice measures X, Bob rotates Ry based on theta).
    """
    def __init__(self, conf: Conf, calc: TFIMCalculator):
        name = f'charge'
        super().__init__(name=name, conf=conf, calc=calc)

    def apply_alice_measurement(self, qc: QuantumCircuit):
        alice_idx = utils.get_alice_idx(self.N)

        qc.h(alice_idx)
        qc.measure(alice_idx, alice_idx)

    def apply_bob_operation(self, qc: QuantumCircuit, xor_alice_res):
        """
        Bob's conditional operation based on Alice's measurement (outcome c).
        Operation is U_B(a) = Ry(a*theta), where a=+1 (c=0) or a=-1 (c=1).
        """
        alice_idx = utils.get_alice_idx(self.N)
        bob_idx = utils.get_bob_idx(self.N)

        theta = self._calc.theta_q1 if not self.theta else self.theta

        # Apply Ry(-theta) if Alice measured '1'.
        qc.ry(-2 * theta, bob_idx).c_if(alice_idx, 1^xor_alice_res)

    def get_bob_measurement_basis(self):
        """
        Bob measures charge density rho = (I + Z) / 2. Requires Z basis.
        """
        return "Z"

    def get_value(self, bitstring: str):
        """
        Extracts the eigenvalue for Bob's charge density operator rho = (I + Z) / 2.
        rho|+> = 1|+> (Eigenvalue 1, measurement '0')
        rho|-> = 0|-> (Eigenvalue 0, measurement '1')
        """
        bob_idx = utils.get_bob_idx(self.N)
        bob_measurement_bit = utils.get_bit_from_counts(bitstring, bob_idx, self.N)

        if bob_measurement_bit == '0':
            return 1.0 # Z eigenvalue +1 -> charge density eigenvalue 1
        else:
            return 0.0 # Z eigenvalue -1 -> charge density eigenvalue 0

    def get_theoretical_gs_expectation_value(self):
        return self._calc.bob_charge

    def description(self):
        bob_idx = utils.get_bob_idx(self.N)
        return f"Bob's Charge Density (I+Z{bob_idx})/2"