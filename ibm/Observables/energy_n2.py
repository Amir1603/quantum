import numpy as np
from qiskit import QuantumCircuit
from .observable import Observable

class Energy_N2(Observable):
    def __init__(self, name, conf):
        super().__init__(name, conf)
        if self.N != 2:
             raise ValueError("Energy_N2 only supports N=2")

    def apply_alice_measurement(self, qc: QuantumCircuit, alice_qubit, alice_creg):
        """
        Alice's measurement for Energy_N2.
        """
        qc.h(alice_qubit)  # Apply Hadamard to ancillary qubit
        qc.measure(alice_qubit, alice_creg)

    def apply_bob_operation(self, qc: QuantumCircuit, bob_qubit, alice_creg, xor_alice_res):
        """
        Bob's conditional operation for Energy_N2.
        """
        theta = self._calc.theta_E1 if not self.theta else self.theta

        with qc.if_test((alice_creg, 0^xor_alice_res)):
            qc.ry(2 * theta, bob_qubit)

        with qc.if_test((alice_creg, 1^xor_alice_res)):
            qc.ry(-2 * theta, bob_qubit)
