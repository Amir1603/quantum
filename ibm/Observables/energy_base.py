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

    def apply_bob_operation(self, qc: QuantumCircuit, xor_alice_res):
        """
        Bob's conditional operation (rotation).
        """
        alice_idx = utils.get_alice_idx(self.N)
        bob_idx = utils.get_bob_idx(self.N)

        theta = self._calc.theta_E1 if not self.theta else self.theta

        qc.ry(2 * theta, bob_idx).c_if(alice_idx, 0^xor_alice_res)
        qc.ry(-2 * theta, bob_idx).c_if(alice_idx, 1^xor_alice_res)
