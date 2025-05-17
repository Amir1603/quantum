from Calculators.tfim_calculator import TFIMCalculator
from qiskit import QuantumCircuit
from .observable import Observable
from conf import Conf

class EnergyBase(Observable):
    def __init__(self, name, conf: Conf, calc: TFIMCalculator):
        super().__init__(name, conf, calc)

    def apply_alice_measurement(self, qc: QuantumCircuit, alice_qubit, alice_creg):
        """
        Alice's  energy measurement.
        """
        qc.h(alice_qubit)
        qc.measure(alice_qubit, alice_creg)

    def apply_bob_operation(self, qc: QuantumCircuit, bob_qubit, alice_creg, xor_alice_res):
        """
        Bob's conditional operation (rotation).
        """
        theta = self._calc.theta_E1 if not self.theta else self.theta

        with qc.if_test((alice_creg, 0^xor_alice_res)):
            qc.ry(2 * theta, bob_qubit)

        with qc.if_test((alice_creg, 1^xor_alice_res)):
            qc.ry(-2 * theta, bob_qubit)
