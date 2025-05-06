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
        # Ensure theta is available
        if self.theta is None:
            # This should not happen if calculated in main.py, but add robustness
            raise ValueError(f"Theta is None for observable {self.name}. Cannot apply Bob's operation.")
            # Or, apply a default rotation, but this deviates from the protocol
            # print(f"Warning: Theta is None for {self.name}. Using default 0 rotation.")
            # protocol_theta = 0.0

        protocol_theta = self.theta # Use the theta calculated and stored
        bob_op_basis = 'Y' if self.alice_basis == 'X' else 'X'
        # Use (-1)^b scaling directly: angle = protocol_theta * (-1)^b
        # b=0 -> angle = +theta; b=1 -> angle = -theta
        angle_if_0 = protocol_theta # rotation for b=0 is exp(-i * theta * sigma_B) -> angle +theta in Ry/Rx
        angle_if_1 = -protocol_theta # rotation for b=1 is exp(+i * theta * sigma_B) -> angle -theta in Ry/Rx

        # Apply correct angle based on b XOR xor_alice_res
        target_b_0 = 0 ^ xor_alice_res
        target_b_1 = 1 ^ xor_alice_res

        print(f"Applying Bob Op: Basis={bob_op_basis}, Theta={protocol_theta:.3f}, XOR={xor_alice_res}")

        # We want exp(-i * theta * (-1)^b_eff * sigma_B) where b_eff = b ^ xor_alice_res
        # Qiskit Rx(a), Ry(a) implement exp(-i * a/2 * X/Y)
        # So rotation angle in Qiskit gates should be a = 2 * theta * (-1)^b_eff
        qiskit_angle_if_0 = 2 * angle_if_0 # Angle for b_eff=0
        qiskit_angle_if_1 = 2 * angle_if_1 # Angle for b_eff=1

        if bob_op_basis == 'Y':
            with qc.if_test((alice_creg, target_b_0)):
                qc.ry(qiskit_angle_if_0, bob_qubit_idx)
            with qc.if_test((alice_creg, target_b_1)):
                qc.ry(qiskit_angle_if_1, bob_qubit_idx)
        elif bob_op_basis == 'X':
            with qc.if_test((alice_creg, target_b_0)):
                qc.rx(qiskit_angle_if_0, bob_qubit_idx)
            with qc.if_test((alice_creg, target_b_1)):
                qc.rx(qiskit_angle_if_1, bob_qubit_idx)