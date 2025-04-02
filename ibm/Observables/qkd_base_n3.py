import numpy as np
from qiskit import QuantumCircuit, ClassicalRegister
from .observable import Observable
from conf import Conf

class QKDBaseN3(Observable):
    """Base class for N=3 QKD protocol measurement observables."""
    def __init__(self, name_suffix: str, conf: Conf, alice_basis: str):
        # Ensure Observable.__init__ sets self.J_param for N=3
        super().__init__(f"qkd_{name_suffix}_n3_alice_{alice_basis.lower()}", conf)
        self.alice_basis = alice_basis.upper()
        if self.N != 3: raise ValueError(f"{self.__class__.__name__} only supports N=3")
        if self.alice_basis not in ['X', 'Y']: raise ValueError("Alice basis must be 'X' or 'Y'")

    # apply_ground_state is inherited from Observable (using numerical method)

    def apply_alice_measurement(self, qc: QuantumCircuit, alice_qubit_idx: int, alice_creg):
        """Alice measures site 0 in X or Y basis."""
        if self.alice_basis == 'X':
            qc.h(alice_qubit_idx)
        elif self.alice_basis == 'Y':
            qc.sdg(alice_qubit_idx)
            qc.h(alice_qubit_idx)
        # Assumes alice_creg is the correct ClassicalRegister bit object
        qc.measure(alice_qubit_idx, alice_creg)

    def apply_bob_operation(self, qc: QuantumCircuit, bob_qubit_idx: int, alice_creg, xor_alice_res: int):
        """Bob's conditional rotation on site 2 (N-1)."""
        protocol_theta = self.theta if self.theta is not None else np.pi / 4 # Placeholder theta
        bob_op_basis = 'Y' if self.alice_basis == 'X' else 'X'
        angle_if_0 = 2 * protocol_theta
        angle_if_1 = -2 * protocol_theta

        # print(f"Applying Bob Op: Basis={bob_op_basis}, Theta={protocol_theta:.3f}, XOR={xor_alice_res}")
        if bob_op_basis == 'Y':
             with qc.if_test((alice_creg, 0 ^ xor_alice_res)):
                  qc.ry(angle_if_0, bob_qubit_idx)
             with qc.if_test((alice_creg, 1 ^ xor_alice_res)):
                  qc.ry(angle_if_1, bob_qubit_idx)
        elif bob_op_basis == 'X':
             with qc.if_test((alice_creg, 0 ^ xor_alice_res)):
                  qc.rx(angle_if_0, bob_qubit_idx)
             with qc.if_test((alice_creg, 1 ^ xor_alice_res)):
                  qc.rx(angle_if_1, bob_qubit_idx)