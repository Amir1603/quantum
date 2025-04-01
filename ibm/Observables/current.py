from conf import Conf
from constants import *
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
from .observable import Observable

class Current(Observable):
    def __init__(self, conf: Conf, apply_protocol):
        self.apply_protocol = apply_protocol
        name = f'current{"" if apply_protocol else "_no_protocol"}'

        # Store h, k for ground state preparation
        self.h = conf.h
        self.k = conf.k
        # Initialize Observable parent class
        super().__init__(name, self.h, self.k)


    def apply_ground_state(self, qc: QuantumCircuit, qubits: list):
        """
        Prepares the ground state of the 2-qubit TFIM.
        Angle depends on h, k. Uses -3pi/4 for critical point h=k.
        """
        denominator = np.sqrt(self.h**2 + self.k**2)
        if denominator == 0:
            # Default to critical angle if h=k=0 (or handle as error/warning)
            theta = -3 * np.pi / 8
            print("Warning: h=k=0, using fixed theta for critical TFIM g.s.")
        else:
            # Calculate theta for general h, k based on ground state formula
            # cos(theta)|00> + sin(theta)|11> state needs Ry(2*theta) gate
            theta = -np.arccos(
                (1 / np.sqrt(2)) * np.sqrt(1 - self.h / denominator)
            )

        # Apply state preparation gates
        qc.ry(2 * theta, qubits[ALICE_QUBIT_IDX]) # Apply Ry to Alice's qubit
        qc.cx(qubits[ALICE_QUBIT_IDX], qubits[BOB_QUBIT_IDX]) # CNOT Alice -> Bob

    def apply_alice_measurement(self, qc: QuantumCircuit, alice_qubit, alice_creg):
        """
        Alice measures charge density (rho ~ Z).
        Measure Alice's qubit in the Z basis.
        """
        qc.measure(alice_qubit, alice_creg) # Measure Z basis

    def apply_bob_operation(self, qc: QuantumCircuit, bob_qubit, alice_creg, xor_alice_res):
        """
        Bob's conditional operation based on Alice's Z measurement (outcome m).
        Apply Ry(pi) if Alice measured '1' (m=1 -> eigenvalue a=-1).
        U_B(a) = Ry(a*pi)
        """
        if self.apply_protocol:
            # Apply Ry(pi) if the classical register (alice_creg) is 1
            qc.ry(np.pi, bob_qubit).c_if(alice_creg, 1^xor_alice_res)

    def get_bob_measurement_basis(self):
        """
        Returns the final measurement basis performed by hardware/simulator
        AFTER basis change gates have been applied. We return Y and effectively
        Sdg+H will be added to the circuit and measurement will be in Z basis.
        """
        return "Y"

    def get_value(self, bitstring: str):
        """
        Extracts the eigenvalue for Bob's intended Y-basis measurement
        from the Z-basis measurement outcome in the counts bitstring
        (obtained after applying Sdg and H gates).

        Mapping:
        - Intended state |+i>_Y -> (Sdg, H) -> |0> -> Measured '0' -> Eigenvalue +1
        - Intended state |-i>_Y -> (Sdg, H) -> |1> -> Measured '1' -> Eigenvalue -1
        """
        bob_measurement_result = bitstring[COUNTS_BOB_QUBIT_IDX]

        if bob_measurement_result == '0':
            return 1.0  # Corresponds to eigenvalue +1 of Y operator
        else:
            return -1.0 # Corresponds to eigenvalue -1 of Y operator

    def description(self):
        return "Y (current)"

    # Note: get_bob_current_outcome might be redundant if get_value serves the purpose
    def get_bob_current_outcome(self, bitstring: str):
        """
        DEPRECATED/REDUNDANT?: Extracts Bob's measurement outcome (+1 or -1 eigenvalue).
        Use get_value directly.
        """
        return self.get_value(bitstring)
