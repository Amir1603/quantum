from conf import Conf
import numpy as np
from qiskit import QuantumCircuit
from .observable import Observable
import utils

class Current(Observable):
    def __init__(self, conf: Conf):
        name = f'current'

        # Initialize Observable parent class
        super().__init__(name, conf)

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
        # Apply Ry(pi) if the classical register (cond) is 1
        with qc.if_test((alice_creg, 1^xor_alice_res)):
            qc.ry(np.pi, bob_qubit)

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
        bob_measurement_result = utils.get_bit_from_counts(bitstring, utils.get_bob_idx(self.N), self.N)

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
