from conf import Conf
from constants import *
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
from .observable import Observable


class Charge(Observable):
    def __init__(self, conf: Conf, apply_protocol):
        self.apply_protocol = apply_protocol
        name = f'charge{'' if apply_protocol else '_no_protocol'}'
        super().__init__(name, SparsePauliOp.from_list([
            ("II", 0.5),
            ("ZI", 0.5),
            ("IZ", 0.5),
            ("ZZ", 0.5)
        ]),
        conf.h,
        conf.k)

    def apply_ground_state(self, qc: QuantumCircuit, qubits: list):
        """
        Prepares the ground state for Charge.
        """
        theta = -np.arccos(
            (1 / np.sqrt(2)) * np.sqrt(1 - self.h / np.sqrt(self.h**2 + self.k**2))
        )
        qc.ry(2 * theta, qubits[0])
        qc.cx(qubits[0], qubits[1])

    def apply_alice_measurement(self, qc: QuantumCircuit, alice_qubit, alice_creg):
        """
        Alice measures the chirality using the projection operator P(b) = 1/2 (1 - (-1)^b X)
        This is equivalent to measuring in the X basis.
        """
        qc.h(alice_qubit)  # Apply Hadamard to measure in X basis
        qc.measure(alice_qubit, alice_creg)

    def apply_bob_operation(self, qc: QuantumCircuit, bob_qubit, alice_creg):
        """
        Bob's operation is a conditional Ry rotation: U(b) = exp(-i * b * pi * Z / 2) -> Ry(b * pi)
        where 'b' is Alice's measurement result (+1 or -1).
        Since Ry(pi) and Ry(-pi) are equivalent, we can simplify to a single conditional.
        """
        if self.apply_protocol:
            # Apply Ry(pi) if Alice measured '1'.
            qc.ry(np.pi, bob_qubit).c_if(alice_creg, 1)
        else:
            pass  # No operation if protocol is not applied

    def get_bob_measurement_basis(self):
        """
        Bob measures in the Z basis to measure the charge density operator (I + Z) / 2
        """
        return "Z"

    def get_operator(self, site):
        """
        For a single site, the charge density operator is (I + Z) / 2.
        The eigenvalue is 1 if the measurement is 0, and 0 if the measurement is 1.
        """
        if site == "alice" or site == "bob":
            return "Z"
        else:
            raise ValueError("Invalid site specified")

    def get_value(self, bitstring: str):
        """
        For a single site, the charge density operator is (I + Z) / 2.
        The eigenvalue is 1 if the measurement is 0, and 0 if the measurement is 1.
        We consider '0' as the positive outcome.
        """
        if bitstring[BOB_QUBIT_IDX] == '0':
            return 1
        else:
            return 0

    def description(self):
        return "I+Z (J_0)"

    def get_bob_charge(self, bitstring: str):
        """
        Extracts Bob's charge from the measurement bitstring.
        """
        return int(bitstring[BOB_QUBIT_IDX])
