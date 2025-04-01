from constants import *
import numpy as np
from qiskit import QuantumCircuit
from .observable import Observable

class Energy(Observable):
    def __init__(self, name, h, k):
        super().__init__(name, h, k)

    def apply_ground_state(self, qc: QuantumCircuit, qubits: list):
        """
        Prepares the ground state for Energy.
        """
        theta = -np.arccos(
            (1 / np.sqrt(2)) * np.sqrt(1 - self.h / np.sqrt(self.h**2 + self.k**2))
        )
        qc.ry(2 * theta, qubits[0])
        qc.cx(qubits[0], qubits[1])

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
        phi = np.arcsin(
            (self.h * self.k) / np.sqrt((self.h**2 + 2 * self.k**2)**2 + self.h**2 * self.k**2)
        ) / 2
        qc.ry(2 * phi, bob_qubit).c_if(alice_creg, 0^xor_alice_res)
        qc.ry(-2 * phi, bob_qubit).c_if(alice_creg, 1^xor_alice_res)
