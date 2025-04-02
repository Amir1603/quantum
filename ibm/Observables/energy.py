from constants import *
import numpy as np
from qiskit import QuantumCircuit
from .observable import Observable

class Energy(Observable):
    def __init__(self, name, h, k, theta):
        super().__init__(name, h, k, theta)

    def apply_alice_measurement(self, qc: QuantumCircuit, alice_qubit, alice_creg):
        """
        Alice's measurement for Energy.
        """
        qc.h(alice_qubit)  # Apply Hadamard to ancillary qubit
        qc.measure(alice_qubit, alice_creg)

    def apply_bob_operation(self, qc: QuantumCircuit, bob_qubit, alice_creg, xor_alice_res):
        """
        Bob's conditional operation for Energy.
        """
        theta = np.arcsin(
                (self.h * self.k) / np.sqrt((self.h**2 + 2 * self.k**2)**2 + self.h**2 * self.k**2)
            ) / 2 if not self.theta else self.theta

        qc.ry(2 * theta, bob_qubit).c_if(alice_creg, 0^xor_alice_res)
        qc.ry(-2 * theta, bob_qubit).c_if(alice_creg, 1^xor_alice_res)
