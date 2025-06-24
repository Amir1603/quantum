from Calculators.tfim_calculator import TFIMCalculator
from qiskit import QuantumCircuit
from .observable import Observable
from conf import Conf
import utils

class EnergyBase(Observable):
    def __init__(self, name, conf: Conf, calc: TFIMCalculator):
        super().__init__(name, conf, calc)

    def apply_alice_measurement(self, qc: QuantumCircuit):
        """
        Alice's energy measurement.
        """
        alice_idx = utils.get_alice_idx(self.N)

        qc.h(alice_idx)
        qc.measure(alice_idx, alice_idx)

    def apply_bob_operation(self, qc: QuantumCircuit, xor_res):
        """
        Bob's conditional operation (rotation).
        """
        alice_idx = utils.get_alice_idx(self.N)
        bob_idx = utils.get_bob_idx(self.N)

        theta = self._calc.theta_Ex if not self.theta else self.theta
        angle = -2 * theta if xor_res == 0 else 2 * theta

        # Apply the controlled rotation based on Alice's measurement.
        # `if_test` is not supported on real hardware, andfor some reason `c_if` is not working.
        # => We use a workaround suggested by Kazuki.
        qc.cry(angle, alice_idx, bob_idx)
        qc.x(alice_idx)
        qc.cry(-angle, alice_idx, bob_idx)
        qc.x(alice_idx)
        # This is equivalent to:
        ###  with qc.if_test((alice_idx, 0^xor_alice_res)):
        ###     qc.ry(2 * theta, bob_idx)
        ### with qc.if_test((alice_idx, 1^xor_alice_res)):
        ###     qc.ry(-2 * theta, bob_idx)
