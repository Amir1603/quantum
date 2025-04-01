from conf import Conf
from constants import *
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
from .observable import Observable


class Charge(Observable):
    def __init__(self, conf: Conf, apply_protocol: bool, theta: float = np.pi):
        self.apply_protocol = apply_protocol
        # TODO
        ## Include theta in the name for clarity when running sweeps
        #protocol_tag = f'_theta{theta/np.pi:.2f}pi' if apply_protocol else '_no_protocol'
        protocol_tag = '' if apply_protocol else '_no_protocol'
        name = f'charge{protocol_tag}'

        if conf.n_qubits - BOB_QUBIT_IDX - 1 < 0:
             raise ValueError("BOB_QUBIT_IDX is out of bounds")

        super().__init__(name, conf.h, conf.k, conf.theta)

    def apply_alice_measurement(self, qc: QuantumCircuit, alice_qubit, alice_creg):
        """
        Alice measures current/chirality ~ sigma_x.
        This requires measuring in the X basis (H + Z measure).
        """
        qc.h(alice_qubit)  # Apply Hadamard to measure in X basis
        qc.measure(alice_qubit, alice_creg)

    def apply_bob_operation(self, qc: QuantumCircuit, bob_qubit, alice_creg, xor_alice_res):
        """
        Bob's conditional operation based on Alice's X measurement (outcome m).
        Operation is U_B(a) = Ry(a*theta), where a=+1 (m=0) or a=-1 (m=1).
        We implement by applying Ry(-theta) if Alice measured '1' (a=-1).
        """
        if self.apply_protocol:
            theta = np.arcsin(
                (self.h * self.k) / np.sqrt((self.h**2 + 2 * self.k**2)**2 + self.h**2 * self.k**2)
            ) / 2 if not self.theta else self.theta

            # Apply Ry(-theta) if Alice measured '1'.
            qc.ry(-2 * theta, bob_qubit).c_if(alice_creg, 1^xor_alice_res)

    def get_bob_measurement_basis(self):
        """
        Bob measures charge density rho = (I + Z) / 2. Requires Z basis.
        """
        return "Z"

    def get_value(self, bitstring: str):
        """
        Extracts the eigenvalue for Bob's charge density operator rho = (I + Z) / 2.
        rho|+> = 1|+> (Eigenvalue 1, measurement '0')
        rho|-> = 0|-> (Eigenvalue 0, measurement '1')
        """
        bob_measurement_result = bitstring[COUNTS_BOB_QUBIT_IDX]

        if bob_measurement_result == '0':
            return 1.0 # Eigenvalue 1
        else:
            return 0.0 # Eigenvalue 0

    def get_gs_expectation_value(self):
        return 0.5 * self.h / np.sqrt(self.h**2 + self.k**2)

    def description(self):
        return "rho = (I+Z)/2"
