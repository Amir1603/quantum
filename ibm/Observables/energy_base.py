from Calculators.tfim_calculator import TFIMCalculator
from qiskit import QuantumCircuit
from .observable import Observable
from conf import Conf
import utils

class EnergyBase(Observable):
    def __init__(self, name, conf: Conf, alice_basis: str, calc: TFIMCalculator):
        super().__init__(name, conf, alice_basis, calc)

    def apply_alice_measurement(self, qc: QuantumCircuit):
        """
        Alice's energy measurement.
        """
        alice_idx = utils.get_alice_idx(self.N)
        utils.apply_basis(qc, self._alice_basis, alice_idx)

        qc.measure(alice_idx, alice_idx)

    def apply_bob_operation(self, qc: QuantumCircuit, xor_res):
        """
        Bob's conditional operation (rotation).
        """
        alice_idx = utils.get_alice_idx(self.N)
        bob_idx = utils.get_bob_idx(self.N)

        theta = self._calc.theta_Ex if not self.theta else self.theta
        angle = -2 * theta if xor_res == 0 else 2 * theta

        # If Alice's basis is 'X', Bob uses 'Y' rotation and vice versa.
        if self._alice_basis == 'X':
            # Apply the controlled rotation based on Alice's measurement.
            # `if_test` is not supported on real hardware, andfor some reason `c_if` is not working.
            # => We use a workaround suggested by Kazuki.
            qc.cry(angle, alice_idx, bob_idx)
            qc.x(alice_idx)
            qc.cry(-angle, alice_idx, bob_idx)
            qc.x(alice_idx)
        elif self._alice_basis == 'Y':
            qc.crx(angle, alice_idx, bob_idx)
            qc.x(alice_idx)
            qc.crx(-angle, alice_idx, bob_idx)
            qc.x(alice_idx)
        else:
            raise ValueError(f"Unsupported Alice basis '{self._alice_basis}'.")

        # This is equivalent to:
        ###  with qc.if_test((alice_idx, 0^xor_alice_res)):
        ###     qc.ry(2 * theta, bob_idx)
        ### with qc.if_test((alice_idx, 1^xor_alice_res)):
        ###     qc.ry(-2 * theta, bob_idx)
